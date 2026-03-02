import json
from pathlib import Path
from typing import Dict, Any, Tuple
from app.services.openrouter import OpenRouterClient
from app.services.extractor import extract_json_from_response, calculate_cost
from app.core.config import settings

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

class Verifier:
    def __init__(self, client: OpenRouterClient):
        self.client = client
        self.grok_prompt = (PROMPTS_DIR / "verify_grok.txt").read_text(encoding="utf-8")
        self.gemini_prompt = (PROMPTS_DIR / "verify_gemini.txt").read_text(encoding="utf-8")
        
        self.model_grok = settings.MODEL_VERIFY_GROK
        self.model_gemini = settings.MODEL_VERIFY_GEMINI

    async def _verify(self, model: str, prompt_template: str, stage1_result: Dict[str, Any]) -> Tuple[Dict[str, Any], int, int, float]:
        stage1_text = json.dumps(stage1_result, ensure_ascii=False, indent=2)
        prompt = prompt_template.replace("{stage1_result}", stage1_text)
        
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        resp = await self.client.chat(
            model=model,
            messages=messages,
            max_tokens=2048,
            temperature=0.2,
        )
        
        content = resp["choices"][0]["message"]["content"]
        usage = resp.get("usage", {"prompt_tokens": 0, "completion_tokens": 0})
        
        in_tokens = usage.get("prompt_tokens", 0)
        out_tokens = usage.get("completion_tokens", 0)
        cost = calculate_cost(model, in_tokens, out_tokens)
        
        result_json = extract_json_from_response(content)
        return result_json, in_tokens, out_tokens, cost

    async def verify_grok(self, stage1_result: Dict[str, Any]) -> Tuple[Dict[str, Any], int, int, float]:
        return await self._verify(self.model_grok, self.grok_prompt, stage1_result)

    async def verify_gemini(self, stage1_result: Dict[str, Any]) -> Tuple[Dict[str, Any], int, int, float]:
        return await self._verify(self.model_gemini, self.gemini_prompt, stage1_result)

    def merge_results(self, grok_res: Tuple[Dict[str, Any], int, int, float] | None, 
                      gemini_res: Tuple[Dict[str, Any], int, int, float] | None) -> Dict[str, Any]:
        """Merge the two sets of JSON responses into a single combined one"""
        merged = {}
        
        grok_data = grok_res[0] if grok_res else {}
        gemini_data = gemini_res[0] if gemini_res else {}
        
        merged["existence_verified"] = grok_data.get("existence_verified", False) or gemini_data.get("official_verified", False)
        merged["status"] = grok_data.get("current_status", "unknown")
        merged["community_sentiment"] = grok_data.get("community_sentiment", "unknown")
        
        merged["highlights"] = grok_data.get("discussion_highlights", [])
        merged["issues"] = grok_data.get("known_issues", [])
        merged["trend"] = grok_data.get("trend", "unknown")
        
        merged["github"] = gemini_data.get("github_stats", {})
        merged["competitors"] = gemini_data.get("competitors", [])
        merged["corrections"] = gemini_data.get("fact_corrections", [])
        
        # Calculate combined confidence
        conf_g = grok_data.get("confidence", 0) if grok_data else 0
        conf_gem = gemini_data.get("confidence", 0) if gemini_data else 0
        
        if grok_data and gemini_data:
            merged["confidence"] = (conf_g + conf_gem) / 2
        elif grok_data:
            merged["confidence"] = conf_g
        elif gemini_data:
            merged["confidence"] = conf_gem
        else:
            merged["confidence"] = 0
            
        return merged
