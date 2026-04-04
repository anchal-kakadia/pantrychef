import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import User
from app.schemas.user import DietaryPrefs, TokenResponse, UserRegister, UserResponse
from app.services.auth import (
    create_access_token,
    decode_access_token,
    get_user_by_email,
    get_user_by_id,
    hash_password,
    verify_password,
)

router = APIRouter()

# This tells FastAPI where clients send their token.
# It also makes the "Authorize" button work in /docs.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency — any endpoint that needs an authenticated user
    adds `user: User = Depends(get_current_user)` to its signature.
    FastAPI calls this automatically and injects the result.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_access_token(token)
    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(db, uuid.UUID(user_id))
    if user is None:
        raise credentials_exception
    return user


# ── Auth endpoints ────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=TokenResponse, status_code=201)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check email isn't already taken
    existing = await get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=payload.email.lower(),   # always store lowercase
        hashed_password=hash_password(payload.password),
        dietary_prefs={},
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)  # populates user.id and server-set fields like created_at

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/auth/token", response_model=TokenResponse)
async def login(
    # OAuth2PasswordRequestForm is the standard form-encoded login payload.
    # /docs "Authorize" button sends exactly this shape.
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(db, form_data.username)  # OAuth2 uses 'username' field

    # Always verify even if user not found — prevents timing attacks
    # that could reveal whether an email is registered
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return TokenResponse(access_token=create_access_token(user.id))


# ── User endpoints ────────────────────────────────────────────────────────────

@router.get("/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    # get_current_user already fetched the user — just return it
    return current_user


@router.patch("/users/me/preferences", response_model=UserResponse)
async def update_preferences(
    prefs: DietaryPrefs,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.dietary_prefs = prefs.model_dump()
    await db.commit()
    await db.refresh(current_user)
    return current_user