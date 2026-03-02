import base64
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any

class Preprocessor:
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        input_data = {
            "input_type": "screenshot" | "url" | "text",
            "file_path": str (if screenshot),
            "url": str (if url),
            "text": str (if text)
        }
        """
        input_type = input_data.get("input_type")
        
        if input_type == "text":
            return {"type": "text", "content": input_data.get("text", "")}
            
        elif input_type == "url":
            url = input_data.get("url")
            if not url:
                raise ValueError("URL is required for input_type='url'")
            
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, follow_redirects=True)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                    
                text = soup.get_text(separator="\n")
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = "\n".join(chunk for chunk in chunks if chunk)
                
                # Truncate if too long (e.g. 20000 chars)
                text = text[:20000]
                
                return {"type": "text", "content": text}
                
        elif input_type == "screenshot":
            file_path = input_data.get("file_path")
            if not file_path:
                raise ValueError("file_path is required for input_type='screenshot'")
                
            with open(file_path, "rb") as f:
                b64_img = base64.b64encode(f.read()).decode("utf-8")
                
            # Determine extension
            ext = file_path.split(".")[-1].lower()
            if ext == "jpg":
                ext = "jpeg"
                
            return {
                "type": "image",
                "content": b64_img,
                "ext": ext
            }
            
        else:
            raise ValueError(f"Unknown input_type: {input_type}")
