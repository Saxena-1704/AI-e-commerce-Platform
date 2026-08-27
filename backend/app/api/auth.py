from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse
)
from backend.app.auth.security import (
    hash_password,
    verify_password,
    create_access_token
)
from backend.app.auth.security import get_current_user

from backend.app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_admin
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=UserResponse)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):

    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = hash_password(
        user_data.password
    )

    user = User(
        role_id=2,
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hashed_password,
        phone_number=user_data.phone_number,
        status="active"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login")
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        user_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token({
        "sub": str(user.id),
        "role_id": user.role_id
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get("/test-protected")
def test_protected(
    user_id: str = Depends(get_current_user)
):
    return {
        "message": "You are authenticated",
        "user_id": user_id
    }


@router.get("/merchant-test")
def merchant_test(
    current_user: User = Depends(get_current_admin)
):
    return {
        "message": "Welcome to the merchant API",
        "user_id": current_user.id,
        "role_id": current_user.role_id
    }