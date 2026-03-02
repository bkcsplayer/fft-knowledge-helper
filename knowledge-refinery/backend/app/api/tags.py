from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.core.database import get_db
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate, TagResponse
from typing import List

router = APIRouter()

@router.get("", response_model=List[TagResponse])
async def get_tags(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Tag).order_by(desc(Tag.usage_count)))
    return res.scalars().all()

@router.post("", response_model=TagResponse, status_code=201)
async def create_tag(tag_in: TagCreate, db: AsyncSession = Depends(get_db)):
    # Check exists
    res = await db.execute(select(Tag).where(Tag.name == tag_in.name))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tag already exists")
        
    tag = Tag(name=tag_in.name, color=tag_in.color)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag

@router.patch("/{id}", response_model=TagResponse)
async def update_tag(id: int, tag_in: TagUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Tag).where(Tag.id == id))
    tag = res.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
        
    if tag_in.name is not None:
        tag.name = tag_in.name
    if tag_in.color is not None:
        tag.color = tag_in.color
        
    await db.commit()
    await db.refresh(tag)
    return tag

@router.delete("/{id}", status_code=204)
async def delete_tag(id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Tag).where(Tag.id == id))
    tag = res.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
        
    await db.delete(tag)
    await db.commit()
    return None
