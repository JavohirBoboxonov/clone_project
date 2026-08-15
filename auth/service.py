from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserResponse(BaseModel):
    user_id: UUID
    username: str
    first_name: str
    last_name: str
    email: str
    balance: float
    profile_picture: str | None
    is_active: bool
    is_staff: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str