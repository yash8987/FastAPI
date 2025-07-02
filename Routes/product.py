from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Models.product import Product
from Models.user import User
from Schemas.product import ProductCreate, ProductOut
from typing import List
from Auth.dependencies import get_current_user, admin_only
from Database.database import get_db

router = APIRouter()

@router.get("/getProducts", response_model=List[ProductOut])
def get_all_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.is_premium or current_user.is_admin:
        products = db.query(Product).filter(Product.is_active == True).all()
    else:
        products = db.query(Product).filter(Product.is_active == True, Product.is_premium == False).all()

    return products


