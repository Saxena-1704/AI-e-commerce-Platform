from fastapi import FastAPI
from sqlalchemy import text

from backend.app.database import engine
from backend.app.api.auth import router as auth_router
from backend.app.api.categories import router as category_router
from backend.app.api.products import router as product_router
from backend.app.api.cart import router as cart_router
from backend.app.api.orders import router as order_router
from backend.app.api.payments import router as payment_router

from fastapi import FastAPI



app = FastAPI()

app.include_router(auth_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(cart_router)
app.include_router(order_router)
app.include_router(payment_router)



@app.get("/")
def root():
    return {
        "message": "Ecommerce backend is running"
    }


@app.get("/db-test")
def database_test():

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        return {
            "database": result.scalar()
        }