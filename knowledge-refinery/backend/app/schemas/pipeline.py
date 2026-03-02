from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List

class PipelineLogResponse(BaseModel):
    id: int
    stage: str
    model_used: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    duration_ms: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class PipelineStatus(BaseModel):
    task_id: str
    entry_id: str
    status: str
    current_stage: str
    stages: Dict[str, Any]
    total_cost_usd: float
    started_at: datetime
    completed_at: Optional[datetime] = None

class PipelineLogsResponse(BaseModel):
    entry_id: str
    logs: List[PipelineLogResponse]
    total_cost_usd: float
    total_duration_ms: int
