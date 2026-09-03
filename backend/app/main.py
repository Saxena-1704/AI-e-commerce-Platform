from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.app.database import engine
from backend.app.api.auth import router as auth_router
from backend.app.api.categories import router as category_router
from backend.app.api.products import router as product_router
from backend.app.api.cart import router as cart_router
from backend.app.api.orders import router as order_router
from backend.app.api.payments import router as payment_router
from backend.app.api.merchant import router as merchant_router
from backend.app.api.merchant_agent import router as merchant_agent_router
from backend.app.mcp.server import mcp

from fastapi.responses import JSONResponse
from backend.app.ucp.profile import UCP_PROFILE

from pathlib import Path
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parents[2]
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


mcp_app = mcp.http_app(
    path="/",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp_app.lifespan(app):
        yield


app = FastAPI(lifespan=lifespan)


app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

app.mount("/ucp/mcp", mcp_app)


# Allow the plain-JS frontend (served on a different port during development)
# to call this API. Restrict this list before production deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(cart_router)
app.include_router(order_router)
app.include_router(payment_router)
app.include_router(merchant_router)
app.include_router(merchant_agent_router)


@app.get("/")
def root():
    return {
        "message": "Ecommerce backend is running"
    }


@app.get("/.well-known/ucp")
def get_ucp_profile():
    return JSONResponse(content=UCP_PROFILE)


@app.get("/db-test")
def database_test():

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        return {
            "database": result.scalar()
        }