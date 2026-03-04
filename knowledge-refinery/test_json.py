import re
import json

sample_text = """
Failed to parse JSON from LLM: ```json
{
  "official_verified": true,
  "official_url": "https://arxiv.org/abs/2301.00250",
  "github_url": "https://github.com/ruvnet/wifi-densepose",
  "github_stats": {
    "stars": 2100
  }
}
```
"""

def extract_json_from_response(text: str) -> dict:
    text = text.strip()
    
    # 1. First attempt: Strict Markdown Code Block Extraction
    match_cmd = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match_cmd:
        json_candidate = match_cmd.group(1).strip()
        print("Regex found candidate:")
        print(repr(json_candidate))
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError on regex: {e}")
            pass # Fall through to brace extraction
            
    # 2. Second attempt: Brace extraction (robust against trailing text)
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_candidate = text[start_idx:end_idx+1]
        print("Brace found candidate:")
        print(repr(json_candidate))
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError on brace: {e}")
            pass # Fall through to desperation fallback
            
    # 3. Last fallback Attempt: Let standard json try (likely fails)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM: {text[:200]}... Error: {e}")

try:
    print(extract_json_from_response(sample_text))
except Exception as e:
    print(e)
