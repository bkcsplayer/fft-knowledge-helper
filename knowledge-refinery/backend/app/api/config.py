from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.model_config import ModelConfig
from typing import List
from pydantic import BaseModel

class ConfigUpdate(BaseModel):
    model_id: str
    max_tokens: int
    temperature: float

class ConfigResponse(BaseModel):
    id: int
    stage: str
    model_id: str
    display_name: str
    is_active: bool
    max_tokens: int
    temperature: float
    
    class Config:
        from_attributes = True

router = APIRouter()

@router.get("/models", response_model=dict)
async def get_models_config(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ModelConfig))
    models = res.scalars().all()
    
    # Initialize defaults if empty
    if not models:
        defaults = [
            ModelConfig(stage="extract", model_id="anthropic/claude-3.5-sonnet", display_name="Claude Sonnet 3.5 (提纯)", max_tokens=2048, temperature=0.2),
            ModelConfig(stage="verify_grok", model_id="x-ai/grok-3", display_name="Grok 3 (社区验证)", max_tokens=2048, temperature=0.3),
            ModelConfig(stage="verify_gemini", model_id="google/gemini-2.5-pro", display_name="Gemini 2.5 Pro (事实验证)", max_tokens=2048, temperature=0.2),
            ModelConfig(stage="analyze", model_id="anthropic/claude-opus-4-6", display_name="Claude Opus 4.6 (深度分析)", max_tokens=4096, temperature=0.4),
        ]
        db.add_all(defaults)
        await db.commit()
        res = await db.execute(select(ModelConfig))
        models = res.scalars().all()

    return {"models": [ConfigResponse.model_validate(m) for m in models]}

@router.put("/models/{id}", response_model=ConfigResponse)
async def update_model_config(id: int, conf_in: ConfigUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ModelConfig).where(ModelConfig.id == id))
    conf = res.scalar_one_or_none()
    if not conf:
        raise HTTPException(status_code=404, detail="Config not found")
        
    conf.model_id = conf_in.model_id
    conf.max_tokens = conf_in.max_tokens
    conf.temperature = conf_in.temperature
    
    await db.commit()
    await db.refresh(conf)
    return conf
