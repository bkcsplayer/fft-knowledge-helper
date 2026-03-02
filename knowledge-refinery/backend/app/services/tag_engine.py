from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.tag import Tag
from typing import List

class TagEngine:
    async def process_tags(self, db: AsyncSession, tag_names: List[str]) -> List[Tag]:
        """Look up existing tags by name, create non-existing ones, and return Tag objects."""
        if not tag_names:
            return []
            
        # Standardize tag names
        clean_names = list({str(t).strip()[:100] for t in tag_names if str(t).strip()})
        
        if not clean_names:
            return []

        # Find existing
        result = await db.execute(
            select(Tag).where(Tag.name.in_(clean_names))
        )
        existing_tags = result.scalars().all()
        existing_names = {t.name for t in existing_tags}
        
        # Create missing
        new_names = set(clean_names) - existing_names
        new_tags = [Tag(name=name) for name in new_names]
        
        if new_tags:
            db.add_all(new_tags)
            await db.flush() # flush to get IDs, avoiding commit
            
        return existing_tags + new_tags
