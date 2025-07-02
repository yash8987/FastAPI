from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    is_premium: bool
    created_at: datetime
    
    class Config:
        orm_mode = True  

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UpdatePremiumStatus(BaseModel):
    is_premium: bool
    

class UpdateAdminStatus(BaseModel):
    is_admin: bool

