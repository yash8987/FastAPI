from fastapi import FastAPI
from Database.database import Base, engine
from Routes.auth import router as auth_router
from Routes.product import router as product_router
from Routes.order import router as order_router
from Routes.admin import router as admin_router

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(product_router, prefix="/products", tags=["Products"])
app.include_router(order_router, prefix="/orders", tags=["Orders"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])