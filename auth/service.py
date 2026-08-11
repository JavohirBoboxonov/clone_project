from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserResponse(BaseModel):
    user_id: UUID
    username: str
    email: str
    profile_picture: str | None
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str