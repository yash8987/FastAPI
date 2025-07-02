from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Auth.dependencies import get_current_user
from Models.order import Order, OrderItem
from Models.product import Product
from Models.user import User
from Schemas.order import OrderCreate, OrderOut
from Database.database import get_db
from Utils.email_sender import send_confirmation_email

router = APIRouter()

@router.post("/createOrder", response_model=OrderOut)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total = 0.0
    order = Order(user_id=current_user.id, total_amount=0.0, status="pending")
    db.add(order)
    db.commit()
    db.refresh(order)

    for item in order_data.items:
        product = db.query(Product).filter(Product.id == item.product_id, Product.is_active == True).first()
        if not product or product.stock < item.quantity:
            db.query(OrderItem).filter(OrderItem.order_id == order.id).delete()
            db.delete(order)
            db.commit()
            raise HTTPException(status_code=400, detail=f"Product ID {item.product_id} is unavailable or out of stock")
        if product.is_premium and not current_user.is_premium:
            db.query(OrderItem).filter(OrderItem.order_id == order.id).delete()
            db.delete(order)
            db.commit()
            raise HTTPException(
                status_code=403,
                detail=f"Product '{product.name}' is premium. Only premium users can purchase it."
            )
        item_total = product.price * item.quantity
        order_item = OrderItem(order_id=order.id, product_id=product.id, quantity=item.quantity, price=product.price)
        db.add(order_item)

        product.stock -= item.quantity
        total += item_total

    order.total_amount = total
    db.commit()
    db.refresh(order)
    subject = "Order Confirmation - MyShop"
    body = f"Hi {current_user.name},\n\nYour order #{order.id} has been placed successfully.\nTotal: ₹{order.total_amount:.2f}\n\nThank you for shopping with us!"
    mail_res = send_confirmation_email(current_user.email, subject, body)
    if not mail_res:
        raise HTTPException(status_code=500, detail="Failed to send order confirmation email.")
    return order

@router.get("/myOrders", response_model=list[OrderOut])
def my_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Order).filter(Order.user_id == current_user.id).all()

@router.delete("/orders/{order_id}")
def delete_own_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this order.")

    db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()

    db.delete(order)
    db.commit()
    return {"message": f"Order #{order_id} deleted successfully"}
