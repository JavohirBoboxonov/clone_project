import os
import select
from dotenv import load_dotenv
from auth.service import *
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException, APIRouter, Depends, UploadFile, File, Form
from config.models import User
from config.database import get_db, AsyncSession
from sqlalchemy import select
from auth.function import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    authenticate_user
)
from cachetools import TTLCache
import random
from auth.function import oauth2_bearer, get_current_user, save_image, PROFILE_IMAGES_DIR
from datetime import timedelta, datetime, timezone
import jwt
from typing import Annotated
from expiringdict import ExpiringDict
from config.tasks import send_reset_code_task
router = APIRouter(
    prefix="/auth",
    tags=['auth']
)
username = User.username
password = User.password

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")
ALGORITHM = 'HS256'
ACCESS_TOKEN_LIFETIME = 15
REFRESH_TOKEN_LIFETIME = 7

db_dependency = Annotated[AsyncSession, Depends(get_db)]

@router.post("/register",response_model=UserResponse, status_code=201)
async def register_user(
        username: str =Form(...),
        email: str=Form(...),
        password: str=Form(...),
        profile_picture:UploadFile=File(None),
        db: AsyncSession=Depends(get_db)):
    result = await db.execute(select(User).filter(User.username == username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Bu username allaqachon mavjud")
    result_email = await db.execute(select(User).filter(User.email==email))
    if result_email.scalars().first():
        raise HTTPException(status_code=400, detail="Bu email allaqachon mavjud")

    new_user = User(
        username = username,
        email=email,
        password=get_password_hash(password),
        profile_picture=save_image(profile_picture, PROFILE_IMAGES_DIR)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm=Depends(), db: AsyncSession = Depends(get_db)):
    user = await db.execute(select(User).filter(User.username == form_data.username))
    user = user.scalars().first()
    if not user:
        raise HTTPException(status_code=400, detail='Username yoki parol xato')

    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail='Username yoki parol xato')

    if not user.is_active:
        raise HTTPException(status_code=400, detail='Foydalanuvchi faol emas')
    access_token = create_access_token(data={"sub": str(user.user_id)}, expires_delta=timedelta(minutes=ACCESS_TOKEN_LIFETIME))
    refresh_token = create_refresh_token(data={"sub": str(user.user_id)}, expires_delta=timedelta(days=REFRESH_TOKEN_LIFETIME))
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "data": {
            "username": user.username,
            "email": user.email
        },
        "token_type": "Bearer"
    }

@router.post("/refresh", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = await authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(status_code=400, detail="Username yoki parol xato")
    access_token = create_access_token(data={"sub": str(user.user_id)}, expires_delta=timedelta(minutes=ACCESS_TOKEN_LIFETIME))
    refresh_token = create_refresh_token(data={"sub": str(user.user_id)}, expires_delta=timedelta(days=REFRESH_TOKEN_LIFETIME))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer"
    }

token_blacklist = ExpiringDict(max_len=1000, max_age_seconds=900)

@router.post("/logout", status_code=200)
async def logout(
    token: Annotated[str, Depends(oauth2_bearer)],
    current_user: dict = Depends(get_current_user)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        now = datetime.now(timezone.utc).timestamp()
        remaining = int(exp - now)

        if remaining > 0:
           token_blacklist[token] = remaining

    except JWTError:
        raise HTTPException(status_code=401, detail="Token yaroqsiz")

    return {"detail": "Muvaffaqiyatli chiqildi"}

reset_code_cache = TTLCache(maxsize=1000, ttl=180)


@router.post("/forgot-password", status_code=200)
async def forgot_password(
    email: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="Bu email ro'yxatdan o'tmagan")

    code = str(random.randint(100000, 999999))
    reset_code_cache[email] = code
    send_reset_code_task.delay(email, code)

    return {"detail": "Kodingiz emailga yuborildi"}

@router.post("/verify_code", status_code=200)
async def verify_code(
    email: str=Form(...),
    code: str=Form(...),
):

    cached_code = reset_code_cache.get(email)

    if not cached_code:
        raise HTTPException(status_code=400, detail="Kod muddati tugagan yoki yuborilmagan")

    if cached_code != code:
        raise HTTPException(status_code=400, detail="Kod no`to`gri")

    reset_code_cache[f"verified:{email}"] = True

    return {"detail": "Kod tasdiqlandi, yangi parol kiriting"}

@router.post("/reset-password", status_code=200)
async def reset_password(
    email: str = Form(...),
    new_password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    if not reset_code_cache.get(f"verified:{email}"):
        raise HTTPException(status_code=400, detail="Avval kodni tasdiqlang")

    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    user.password = get_password_hash(new_password)
    await db.commit()
    reset_code_cache.pop(email, None)
    reset_code_cache.pop(f"verified:{email}", None)

    return {"detail": "Parol muvaffaqiyatli yangilandi"}
