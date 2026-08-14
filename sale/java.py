from sys import deactivate_stack_trampoline
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, UploadFile, status, File, Form
from auth.api import register_user
from config.models import Product
from sale.schema import ProductResponseSchema
from config.database import get_db, AsyncSession, DATABASE_URL
from typing import Annotated
from auth.function import get_current_user, save_image, PRODUCT_IMAGES_DIR
from sqlalchemy import select
import shutil
import uuid
import os

router = APIRouter(
    prefix="/products",
    tags=["products"]
)
db_dependency = Annotated[AsyncSession, Depends(get_db)]

@router.get("/products/")
async def get_all_products(limit: int = Query(20, ge=1), offset: int = Query(0, ge=0)):
    query = "SELECT * FROM products ORDER BY product_id LIMIT :limit OFFSET :offset"
    rows = await DATABASE_URL.fetch_all(query=query, values = {"limit": limit, "offset": offset})
    return {"data": rows, "limit": limit, "offset": offset}

@router.get('/product_detail/{product_id}', status_code=204)
async def get_one_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).filter(Product.product_id == product_id))
    product = result.scalars().first()

    if not product_id:
        raise HTTPException(status_code=404, detail='Bu mahsulot topilmadi')
    return product

@router.post('/product_create', response_model=ProductResponseSchema)
async def create_product(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await db.execute(select(Product).filter(Product.title == title))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail='Bu title allaqachon mavjud')

    new_product = Product(
        user_id=current_user['user_id'],
        title=title,
        description=description,
        pictures=save_image(image, PRODUCT_IMAGES_DIR),
        stock=stock,
        price=price,
        total=price*stock
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

@router.patch('/product_update/{product_id}', response_model=ProductResponseSchema)
async def update_product(
    product_id: int,
    title: str = Form(...),
    description: str = Form(...),
    stock: int = Form(...),
    price: int = Form(...),
    image: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    result = await db.execute(select(Product).filter(Product.product_id==product_id))
    product = result.scalars().first()
    
    if not product:
        raise HTTPException(status_code=400, detail="Bu mahsulot topilmadi")

    owner_exit = str(product.user_id) == (current_user['user_id'])
    is_admin = current_user.get('role') == 'admin'

    if not owner_exit or not is_admin:
        raise HTTPException(status_code=403, detail="Siz bu mahsulotni o`zgartish huquqiga ega emassiz")
    
    product.title = title,
    product.description = description,
    product.stock = stock,
    product.price = price,
    product.total = stock * price
    product.pictures = save_image(image, PRODUCT_IMAGES_DIR)

    await db.commit()
    await db.refresh(product)
    return product

@router.delete('/product_delete/{product_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete(product_id: int, db:AsyncSession=Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Product).filter(Product.product_id == product_id))
    product = result.scalars().first()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bu mahsulot topilmadi")

    is_owner = str(product.user_id) == str(current_user['user_id'])
    is_admin = current_user.get('role') == 'admin'

    if not is_admin or not is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Bu mahsulotni ustida amal bajata olmaysiz')

    await db.delete(product)
    await db.commit()

    return HTTPException(status_code=200, detail="Mahsulot o`chirildi")