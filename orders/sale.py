from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config.database import get_db
from config.models import Cart, CartItem, Product, Order, OrderItem, OrderStatus
from auth.function import get_current_user
from orders.schema import CartItemAddSchema, CartResponse, OrderResponse
from typing import Annotated

router = APIRouter(prefix="/shop", tags=["shop"])

@router.get('/cart', response_model=CartResponse)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await db.execute(select(Cart).filter(Cart.user_id == current_user['user_id']))
    cart = result.scalars().first()
    
    if not cart:
        cart = Cart(user_id=current_user['user_id'])
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
    
    return cart

@router.post('/cart/add', response_model=CartResponse)
async def add_to_cart(
    data: CartItemAddSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    product = await db.execute(select(Product).filter(Product.product_id == data.product_id))
    product = product.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
    
    if product.stock < data.quantity:
        raise HTTPException(status_code=400, detail="Yetarli mahsulot yo'q")

    result = await db.execute(select(Cart).filter(Cart.user_id == current_user['user_id']))
    cart = result.scalars().first()
    if not cart:
        cart = Cart(user_id=current_user['user_id'])
        db.add(cart)
        await db.commit()
        await db.refresh(cart)

    item_result = await db.execute(
        select(CartItem).filter(CartItem.cart_id == cart.cart_id, CartItem.product_id == data.product_id)
    )
    item = item_result.scalars().first()
    
    if item:
        item.quantity += data.quantity
    else:
        item = CartItem(cart_id=cart.cart_id, product_id=data.product_id, quantity=data.quantity)
        db.add(item)
    
    await db.commit()
    await db.refresh(cart)
    return cart

@router.delete('/cart/remove/{item_id}', status_code=204)
async def remove_from_cart(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await db.execute(select(CartItem).filter(CartItem.item_id == item_id))
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
    
    await db.delete(item)
    await db.commit()

@router.post('/order/create', response_model=OrderResponse)
async def create_order(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await db.execute(select(Cart).filter(Cart.user_id == current_user['user_id']))
    cart = result.scalars().first()
    
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Savat bo'sh")

    total_price = 0
    order_items = []

    for item in cart.items:
        product = await db.execute(select(Product).filter(Product.product_id == item.product_id))
        product = product.scalars().first()
        
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"{product.title} yetarli emas")
        
        product.stock -= item.quantity
        product.total = product.price * product.stock
        
        item_price = product.price * item.quantity
        total_price += item_price
        
        order_items.append(OrderItem(
            product_id=item.product_id,
            quantity=item.quantity,
            price=item_price
        ))

    order = Order(
        user_id=current_user['user_id'],
        total_price=total_price,
        status=OrderStatus.pending
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    for order_item in order_items:
        order_item.order_id = order.order_id
        db.add(order_item)

    await db.execute(CartItem.__table__.delete().where(CartItem.cart_id == cart.cart_id))
    
    await db.commit()
    await db.refresh(order)
    return order

@router.get('/orders', response_model=list[OrderResponse])
async def get_orders(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await db.execute(select(Order).filter(Order.user_id == current_user['user_id']))
    orders = result.scalars().all()
    return orders

@router.get('/orders/{order_id}', response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await db.execute(
        select(Order).filter(Order.order_id == order_id, Order.user_id == current_user['user_id'])
    )
    order = result.scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    return order