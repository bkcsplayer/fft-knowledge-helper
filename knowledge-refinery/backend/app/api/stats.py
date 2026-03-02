from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.database import get_db
from app.models.entry import KnowledgeEntry
from app.models.tag import Tag
from app.models.pipeline_log import PipelineLog

router = APIRouter()

@router.get("")
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Total entries
    total_res = await db.execute(select(func.count(KnowledgeEntry.id)))
    total_entries = total_res.scalar() or 0
    
    # Cost
    cost_res = await db.execute(select(func.sum(PipelineLog.cost_usd)))
    total_cost = cost_res.scalar() or 0.0
    
    # Categories
    cat_res = await db.execute(select(KnowledgeEntry.category, func.count(KnowledgeEntry.id)).group_by(KnowledgeEntry.category))
    by_category = {row[0]: row[1] for row in cat_res.all()}
    
    # Maturity
    mat_res = await db.execute(select(KnowledgeEntry.maturity, func.count(KnowledgeEntry.id)).group_by(KnowledgeEntry.maturity))
    by_maturity = {row[0]: row[1] for row in mat_res.all()}
    
    # Top tags
    tags_res = await db.execute(select(Tag).order_by(Tag.usage_count.desc()).limit(5))
    top_tags = [{"name": t.name, "count": t.usage_count} for t in tags_res.scalars().all()]
    
    return {
        "total_entries": total_entries,
        "by_category": by_category,
        "by_maturity": by_maturity,
        "total_cost_usd": float(total_cost),
        "top_tags": top_tags
    }
