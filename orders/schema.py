from pydantic import BaseModel
import uuid
from datetime import datetime

class CartItemAddSchema(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemResponse(BaseModel):
    item_id: int
    product_id: int
    quantity: int
    
    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    cart_id: int
    items: list[CartItemResponse] = []
    
    class Config:
        from_attributes = True

class OrderItemResponse(BaseModel):
    order_item_id: int
    product_id: int
    quantity: int
    price: float
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    order_id: int
    status: str
    total_price: float
    created_at: datetime
    items: list[OrderItemResponse] = []
    
    class Config:
        from_attributes = True