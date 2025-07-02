from pydantic import BaseModel
from typing import List
from datetime import datetime

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class OrderItemOut(BaseModel):
    product_id: int
    quantity: int
    price: float

    class Config:
        orm_mode = True

class OrderOut(BaseModel):
    id: int
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItemOut]

    class Config:
        orm_mode = True
