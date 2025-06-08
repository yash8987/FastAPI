from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class EmailSchema(BaseModel):
    recipient: EmailStr
    subject: str
    body: str

class EmailLogSchema(BaseModel):
    id: int
    recipient: str
    subject: str
    body: str
    status: str
    timestamp: datetime

    class Config:
        orm_mode = True