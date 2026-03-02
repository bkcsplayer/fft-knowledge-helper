from pydantic import BaseModel
from datetime import datetime

class ProfileUpdate(BaseModel):
    profile_name: str
    profile_prompt: str

class ProfileResponse(BaseModel):
    id: int
    profile_name: str
    profile_prompt: str
    is_active: bool
    updated_at: datetime

    class Config:
        from_attributes = True
