from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    is_active: Optional[bool] = True
    is_premium: Optional[bool] = False

class ProductOut(ProductCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None
    is_premium: Optional[bool] = None
