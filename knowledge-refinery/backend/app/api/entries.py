import uuid
import os
import shutil
from typing import Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.pipeline import PipelineOrchestrator, TaskState
from app.models.entry import KnowledgeEntry
from app.schemas.entry import EntryDetail, EntryBrief, EntryList, EntryUpdate

router = APIRouter()

@router.post("/upload", status_code=202)
async def upload_entry(
    background_tasks: BackgroundTasks,
    input_type: str = Form(...),           # screenshot | url | text
    pipeline_mode: str = Form("deep"),     # quick | deep
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    entry_id = uuid.uuid4()
    
    input_data = {
        "input_type": input_type,
        "url": url,
        "text": text,
    }
    
    if input_type == "screenshot":
        if not file:
            raise HTTPException(status_code=400, detail="file is required for screenshot")
            
        # Temporarily save
        temp_dir = "/tmp/refinery_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, f"{entry_id}_{file.filename}")
        
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
            
        input_data["file_path"] = file_path

    # Initialize Task State
    task_state = TaskState(entry_id=str(entry_id), mode=pipeline_mode)
    
    # Initialize Pipeline Orchestrator and dispatch
    orchestrator = PipelineOrchestrator(db_session=db)
    background_tasks.add_task(orchestrator.run, entry_id, input_data, task_state)
    
    return {
        "task_id": task_state.task_id,
        "entry_id": str(entry_id),
        "status": "processing",
        "message": f"Pipeline started in {pipeline_mode} mode",
    }

@router.get("", response_model=EntryList)
async def get_entries(
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    tags: Optional[str] = None,
    category: Optional[str] = None,
    maturity: Optional[str] = None,
    actionability: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db)
):
    # Simplified query without complex sorting/filtering for now
    query = select(KnowledgeEntry).options(selectinload(KnowledgeEntry.tags))
    
    if category:
        query = query.where(KnowledgeEntry.category == category)
    if is_favorite is not None:
        query = query.where(KnowledgeEntry.is_favorite == is_favorite)
        
    query = query.order_by(desc(KnowledgeEntry.created_at))
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    res = await db.execute(query)
    entries = res.scalars().unique().all()
    
    # Needs a real total count for pagination
    return {
        "items": entries,
        "total": len(entries),
        "page": page,
        "per_page": per_page,
        "total_pages": 1
    }

@router.get("/{id}", response_model=EntryDetail)
async def get_entry(id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(KnowledgeEntry)
        .where(KnowledgeEntry.id == uuid.UUID(id))
        .options(selectinload(KnowledgeEntry.tags), selectinload(KnowledgeEntry.attachments))
    )
    entry = res.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
        
    # Read md content
    import os
    from app.core.config import settings
    md_content = ""
    try:
        path = os.path.join(settings.KNOWLEDGE_VAULT_PATH, entry.md_file_path)
        with open(path, "r", encoding="utf-8") as f:
            md_content = f.read()
    except Exception:
        pass
        
    entry.__dict__["md_content"] = md_content
    return entry

@router.delete("/{id}", status_code=204)
async def delete_entry(id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.id == uuid.UUID(id)))
    entry = res.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
        
    # delete file
    import os
    from app.core.config import settings
    try:
        path = os.path.join(settings.KNOWLEDGE_VAULT_PATH, entry.md_file_path)
        if os.path.exists(path):
            os.remove(path)
    except:
        pass
    
    await db.delete(entry)
    await db.commit()
    return None
