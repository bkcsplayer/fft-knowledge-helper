from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from typing import List

from app.models.pipeline_log import PipelineLog
from app.core.database import get_db
from app.schemas.pipeline import PipelineStatus, PipelineLogsResponse, PipelineLogResponse

import app.core.pipeline as pipeline_mod
_task_states = pipeline_mod._task_states

router = APIRouter()

@router.get("/status/{task_id}", response_model=PipelineStatus)
async def get_pipeline_status(task_id: str):
    if task_id not in _task_states:
        raise HTTPException(status_code=404, detail="Task not found")
        
    state = _task_states[task_id]
    return state

@router.get("/logs/{entry_id}", response_model=PipelineLogsResponse)
async def get_pipeline_logs(entry_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(PipelineLog)
        .where(PipelineLog.entry_id == uuid.UUID(entry_id))
        .order_by(PipelineLog.created_at)
    )
    logs = res.scalars().all()
    
    total_cost = sum(log.cost_usd for log in logs if log.cost_usd is not None)
    total_duration = sum(log.duration_ms for log in logs if log.duration_ms is not None)
    
    return {
        "entry_id": entry_id,
        "logs": logs,
        "total_cost_usd": total_cost,
        "total_duration_ms": total_duration
    }
