import json
from pathlib import Path
from typing import Dict, Any, Tuple
from app.services.openrouter import OpenRouterClient
from app.services.extractor import extract_json_from_response, calculate_cost
from app.core.config import settings

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

class Analyzer:
    def __init__(self, client: OpenRouterClient):
        self.client = client
        self.prompt_template = (PROMPTS_DIR / "analyze.txt").read_text(encoding="utf-8")
        self.model = settings.MODEL_ANALYZE

    async def analyze(self, stage1_result: Dict[str, Any], stage2_result: Dict[str, Any] | None, 
                      profile_prompt: str, confidence_penalty: float = 0.0) -> Tuple[str, Dict[str, Any], int, int, float]:
        
        stage1_text = json.dumps(stage1_result, ensure_ascii=False, indent=2)
        stage2_text = json.dumps(stage2_result, ensure_ascii=False, indent=2) if stage2_result else "（快速模式，未执行搜索验证）"
        
        prompt = self.prompt_template.replace(
            "{profile_prompt}", profile_prompt
        ).replace(
            "{stage1_result}", stage1_text
        ).replace(
            "{stage2_result}", stage2_text
        )
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        try:
            resp = await self.client.chat(
                model=self.model,
                messages=messages,
                max_tokens=4096,
                temperature=0.4,
            )
        except Exception as e:
            # Fallback to sonnet
            print(f"Analyzer Opus failed: {e}. Falling back to Sonnet.")
            self.model = settings.MODEL_EXTRACT
            resp = await self.client.chat(
                model=self.model,
                messages=messages,
                max_tokens=4096,
                temperature=0.4,
            )
            confidence_penalty += 0.3
            
        content = resp["choices"][0]["message"]["content"]
        usage = resp.get("usage", {"prompt_tokens": 0, "completion_tokens": 0})
        
        in_tokens = usage.get("prompt_tokens", 0)
        out_tokens = usage.get("completion_tokens", 0)
        cost = calculate_cost(self.model, in_tokens, out_tokens)
        
        # Split Markdown content and metadata JSON
        # Output format has ```json at the end
        markdown_body = content
        metadata = {}
        
        if "```json" in content:
            parts = content.split("```json")
            markdown_body = parts[0].strip()
            json_str = parts[1].split("```")[0].strip()
            try:
                metadata = json.loads(json_str)
            except Exception:
                pass
                
        # Apply confidence penalty
        if "confidence" in metadata:
            metadata["confidence"] = max(0.0, float(metadata["confidence"]) - confidence_penalty)
            
        return markdown_body, metadata, in_tokens, out_tokens, cost
