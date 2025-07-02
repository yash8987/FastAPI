from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from Auth.dependencies import get_current_user, admin_only
from Models.user import User
from Models.order import Order, OrderItem
from Models.product import Product
from Schemas.user import UserOut, UpdatePremiumStatus, UserCreate, UpdateAdminStatus
from Schemas.order import OrderOut
from Schemas.product import ProductOut, ProductCreate, ProductUpdate
from Database.database import get_db
from Schemas.admin import AdminStats
from sqlalchemy import func
from Utils.email_sender import send_confirmation_email
from Auth.auth_utils import hash_password


router = APIRouter()

@router.get("/getUsers", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    return db.query(User).all()

@router.get("/getOrders", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    return db.query(Order).all()

@router.get("/getProducts", response_model=List[ProductOut])
def list_all_products(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    return db.query(Product).all()

@router.post("/createProduct", response_model=ProductOut)
def create_product(product: ProductCreate, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

@router.get("/stats", response_model=AdminStats)
def get_admin_stats(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    total_users = db.query(func.count(User.id)).scalar()
    total_orders = db.query(func.count(Order.id)).scalar()
    total_products = db.query(func.count(Product.id)).scalar()
    total_revenue = db.query(func.coalesce(func.sum(Order.total_amount), 0)).scalar()

    return AdminStats(
        total_users=total_users,
        total_orders=total_orders,
        total_products=total_products,
        total_revenue=total_revenue
    )

@router.patch("/admin/orders/{order_id}/complete")
def complete_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = "completed"
    db.commit()

    subject = f"Order #{order.id} Completed"
    body = f"Hi,\n\nYour order #{order.id} has been completed and is on its way!\n\nThank you for shopping!"
    mail_res = send_confirmation_email(order.user.email, subject, body)
    if not mail_res:
        raise HTTPException(status_code=500, detail="Failed to send order confirmation email.")
    return {"message": f"Order #{order.id} marked as completed and customer notified."}

@router.post("/createAdmin", response_model=UserOut)
def create_admin(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only)
):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    new_admin = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        is_admin=True,
        is_active=True
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin

@router.delete("/orders/{order_id}")
def delete_order_by_id(order_id: int, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    db.query(OrderItem).filter(OrderItem.order_id == order.id).delete()

    db.delete(order)
    db.commit()
    
    return {"message": f"Order #{order_id} deleted successfully"}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    if current_user.id == user_id:
        raise HTTPException(status_code=403, detail="You cannot delete your own account.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": f"User ID {user_id} deleted successfully"}

@router.patch("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    updated_data: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in updated_data.dict(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product

@router.patch("/users/{user_id}/premium", response_model=UserOut)
def update_premium_status(
    user_id: int,
    payload: UpdatePremiumStatus,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    previous_status = user.is_premium
    user.is_premium = payload.is_premium
    db.commit()
    db.refresh(user)
    
    if previous_status != user.is_premium:
        if user.is_premium:
            subject = "🎉 You're now a Premium Member!"
            body = f"Hi {user.name},\n\nCongratulations! You’ve been upgraded to a premium member.\nEnjoy exclusive offers and products tailored just for you.\n\nThank you for choosing us!"
        else:
            subject = "⚠️ Premium Membership Ended"
            body = f"Hi {user.name},\n\nYour premium membership has been deactivated.\nYou now have access to regular features.\n\nIf this was unexpected, please contact support."

        mail_res = send_confirmation_email(user.email, subject, body)
        if not mail_res:
            raise HTTPException(status_code=500, detail="Failed to send email.")
    return user

@router.patch("/users/{user_id}/admin", response_model=UserOut)
def update_admin_status(
    user_id: int,
    payload: UpdateAdminStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    if current_user.id == user_id:
        raise HTTPException(status_code=403, detail="You cannot change your own admin status.")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    previous_status = user.is_admin
    user.is_admin = payload.is_admin
    db.commit()
    db.refresh(user)
    
    if previous_status != user.is_admin:
        if user.is_admin:
            subject = "🎉 You've been promoted to Admin!"
            body = f"Hi {user.name},\n\nYou have been granted admin access on your account.\nYou can now manage the platform.\n\nThank you."
        else:
            subject = "⚠️ Admin access removed"
            body = f"Hi {user.name},\n\nYour admin access has been revoked.\nYou now have normal user privileges.\n\nIf you believe this is a mistake, please contact support."

        mail_res = send_confirmation_email(user.email, subject, body)
        if not mail_res:
            raise HTTPException(status_code=500, detail="Failed to send email.")
    return user


