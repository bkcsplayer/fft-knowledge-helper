from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.profile import UserProfile
from app.schemas.profile import ProfileUpdate, ProfileResponse

router = APIRouter()

@router.get("", response_model=ProfileResponse)
async def get_profile(db: AsyncSession = Depends(get_db)):
    # Get active or create default
    res = await db.execute(select(UserProfile).where(UserProfile.is_active == True))
    profile = res.scalar_one_or_none()
    
    if not profile:
        profile = UserProfile(
            profile_name="default",
            profile_prompt="你是一个具有商业头脑的技术战略分析师。"
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        
    return profile

@router.put("", response_model=ProfileResponse)
async def update_profile(profile_in: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(UserProfile).where(UserProfile.is_active == True))
    profile = res.scalar_one_or_none()
    
    if profile:
        profile.profile_name = profile_in.profile_name
        profile.profile_prompt = profile_in.profile_prompt
        await db.commit()
        await db.refresh(profile)
        return profile
    else:
        new_profile = UserProfile(
            profile_name=profile_in.profile_name,
            profile_prompt=profile_in.profile_prompt,
            is_active=True
        )
        db.add(new_profile)
        await db.commit()
        await db.refresh(new_profile)
        return new_profile
