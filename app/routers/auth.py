from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..database import get_db
from ..models import User, Token
from ..security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=Token)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT access token."""
    # Fetch user by username or email
    query = select(User).where(User.username == request.username)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})

    # Build token payload
    token_payload = {
        "sub": str(user.id),
        "username": user.username,
        "access_level": user.access_level,
        "role": user.role,
    }

    access_token = create_access_token(token_payload)
    return Token(access_token=access_token, token_type="bearer") 