import json
import re
from pathlib import Path
from typing import Dict, Any, Tuple
from app.services.openrouter import OpenRouterClient
from app.core.config import settings

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    PRICING = {
        "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
        "x-ai/grok-3": {"input": 3.0, "output": 15.0},
        "google/gemini-2.5-pro": {"input": 1.25, "output": 10.0},
        "anthropic/claude-opus-4-6": {"input": 15.0, "output": 75.0},
    }
    prices = PRICING.get(model, {"input": 0.0, "output": 0.0})
    return (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000

def extract_json_from_response(text: str) -> dict:
    text = text.strip()
    
    # 1. First attempt: Strict Markdown Code Block Extraction
    match_cmd = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match_cmd:
        json_candidate = match_cmd.group(1).strip()
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError:
            pass # Fall through to brace extraction
            
    # 2. Second attempt: Brace extraction (robust against trailing text)
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_candidate = text[start_idx:end_idx+1]
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError:
            pass # Fall through to desperation fallback
            
    # 3. Last fallback Attempt: Let standard json try (likely fails)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM: {text[:200]}... Error: {e}")

class Extractor:
    def __init__(self, client: OpenRouterClient):
        self.client = client
        self.prompt = (PROMPTS_DIR / "extraction.txt").read_text(encoding="utf-8")
        self.model = settings.MODEL_EXTRACT

    async def extract(self, processed_input: Dict[str, Any]) -> Tuple[Dict[str, Any], int, int, float]:
        input_type = processed_input["type"]
        messages = []
        
        if input_type == "image":
            ext = processed_input.get("ext", "png")
            b64 = processed_input["content"]
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{ext};base64,{b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": self.prompt
                    }
                ]
            })
        else:
            text_content = processed_input["content"]
            messages.append({
                "role": "user",
                "content": f"{self.prompt}\n\n【输入内容】\n{text_content}"
            })
            
        resp = await self.client.chat(
            model=self.model,
            messages=messages,
            max_tokens=2048,
            temperature=0.2,
        )
        
        content = resp["choices"][0]["message"]["content"]
        usage = resp.get("usage", {"prompt_tokens": 0, "completion_tokens": 0})
        
        in_tokens = usage.get("prompt_tokens", 0)
        out_tokens = usage.get("completion_tokens", 0)
        cost = calculate_cost(self.model, in_tokens, out_tokens)
        
        result_json = extract_json_from_response(content)
        return result_json, in_tokens, out_tokens, cost
