from fastapi import FastAPI
from sqlalchemy import text

from backend.app.database import engine
from backend.app.api.auth import router as auth_router

app = FastAPI()

app.include_router(auth_router)


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