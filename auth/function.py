import os
import select
from dotenv import load_dotenv
from datetime import timedelta, datetime
from typing import Optional
from fastapi import HTTPException, APIRouter, Depends, status, UploadFile, File
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
import jwt
from typing import Annotated
from config.models import User
import shutil
import uuid

pwd_context = CryptContext(schemes=['argon2'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/users/login")

SECRET_KEY = os.getenv("SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")
ACCESS_TOKEN_LIFETIME = 15
REFRESH_TOKEN_LIFETIME = 7
ALGORITHM = "HS256"

def verify_password(plain_password, password):
    return pwd_context.verify(plain_password, password)
def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_LIFETIME))
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"user_id": user_id}

async def get_base_roleuser(token: Annotated[str, Depends(oauth2_bearer)]):
    credentialials_exception=HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have such a right"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: str = payload.get('user_id')
        is_staff: bool = payload.get('is_staff')

        if username is None or user_id is None:
            raise credentials_exception

        if not is_staff:
            raise credentialials_exception
    
    except Exception as e:
        return credentialials_exception
    
    return {'username': username, "user_id": user_id, "is_staff": is_staff}

PROFILE_IMAGES_DIR = "media/profiles"
PRODUCT_IMAGES_DIR = "media/products"


def save_image(file: UploadFile, directory: str) -> str | None:
    if not file or not file.filename:
        return None

    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Faqat rasm yuklash mumkin")

    os.makedirs(directory, exist_ok=True)
    file_extension = file.filename.split('.')[-1]
    safe_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"{directory}/{safe_filename}"

    with open(file_path, 'wb+') as file_obj:
        shutil.copyfileobj(file.file, file_obj)

    return file_path