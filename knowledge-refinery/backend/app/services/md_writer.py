import os
from datetime import datetime
from slugify import slugify
from jinja2 import Environment, BaseLoader
from app.core.config import settings

FRONTMATTER_TEMPLATE = """---
title: "{{ title }}"
created: {{ created_at }}
updated: {{ updated_at }}
source_type: {{ source_type }}
source_url: {% if source_url %}"{{ source_url }}"{% else %}null{% endif %}
category: {{ category }}
tags:
{% for tag in tags %}  - {{ tag }}
{% endfor %}
confidence: {{ confidence }}
maturity: {{ maturity }}
actionability: {{ actionability }}
pipeline_mode: {{ pipeline_mode }}
related_projects:
{% for p in related_projects %}  - {{ p }}
{% endfor %}
review_notes: {% if review_notes %}"{{ review_notes | replace('"', '\\"') }}"{% else %}null{% endif %}
entry_id: "{{ entry_id }}"
---

"""

class MDWriter:
    def __init__(self):
        self.vault_path = settings.KNOWLEDGE_VAULT_PATH
        self.env = Environment(loader=BaseLoader())

    async def write(self, entry_id: str, stage1_result: dict, analysis_body: str, metadata_result: dict, mode: str, source_type: str, source_url: str = None) -> str:
        title = stage1_result.get("title", "Untitled")
        category = stage1_result.get("category", "other")
        
        # Frontmatter variables
        context = {
            "title": title,
            "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_type": source_type,
            "source_url": source_url,
            "category": category,
            "tags": metadata_result.get("tags", []),
            "confidence": metadata_result.get("confidence", 0.0),
            "maturity": metadata_result.get("maturity", "seed"),
            "actionability": metadata_result.get("actionability", "medium"),
            "pipeline_mode": mode,
            "related_projects": metadata_result.get("related_projects", []),
            "review_notes": metadata_result.get("review_notes", ""),
            "entry_id": str(entry_id)
        }
        
        template = self.env.from_string(FRONTMATTER_TEMPLATE)
        frontmatter = template.render(**context)
        
        full_content = frontmatter + analysis_body
        
        slug = slugify(title)
        date_str = datetime.utcnow().strftime("%Y%m%d")
        short_id = str(entry_id)[:8]
        filename = f"{date_str}-{slug}-{short_id}.md"
        
        file_path = os.path.join(self.vault_path, filename)
        
        # Actually write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)
            
        return filename
