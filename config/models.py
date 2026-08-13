import uuid
import enum
from config.database import Base
from sqlalchemy import (
    Column,
    Integer,
    UUID,
    String,
    Boolean,
    Numeric,
    ForeignKey,
    DateTime,
    Enum
)
from datetime import datetime, timedelta
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base):
    __tablename__ = 'users'
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    profile_picture = Column(String(300), nullable=True)
    email = Column(String(100), unique=True)
    password = Column(String(250))
    balance = Column(Numeric(10, 2), default=0, nullable=False, server_default='0')
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)

    products: Mapped[list["Product"]] = relationship(back_populates="author" ,cascade='all, delete-orphan')
    cart: Mapped["Cart"] = relationship(back_populates='user', uselist=False, cascade='all, delete-orphan')
    orders: Mapped[list["Order"]] = relationship(back_populates='user', cascade='all, delete-orphan')

class Product(Base):
    __tablename__ = 'products'
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    title = Column(String(100), nullable=False, unique=True)
    description = Column(String(500), nullable=False)
    pictures = Column(String(300), nullable=True)
    stock = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False, server_default="0")
    total = Column(Numeric(10, 2), nullable=False, server_default="0")
    
    author: Mapped[list['User']] = relationship(back_populates='products')

class OrderStatus(enum.Enum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"

class Cart(Base):
    __tablename__ = 'carts'
    cart_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user: Mapped["User"] = relationship(back_populates='cart')
    items: Mapped[list["CartItem"]] = relationship(back_populates='cart', cascade='all, delete-orphan')

class CartItem(Base):
    __tablename__ = 'cart_items'
    item_id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey('carts.cart_id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.product_id', ondelete='CASCADE'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    
    cart: Mapped["Cart"] = relationship(back_populates='items')
    product: Mapped["Product"] = relationship()

class Order(Base):
    __tablename__ = 'orders'
    order_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)
    total_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user: Mapped["User"] = relationship(back_populates='orders')
    items: Mapped[list["OrderItem"]] = relationship(back_populates='order', cascade='all, delete-orphan')

class OrderItem(Base):
    __tablename__ = 'order_items'
    order_item_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.order_id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.product_id', ondelete='CASCADE'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    
    order: Mapped["Order"] = relationship(back_populates='items')
    product: Mapped["Product"] = relationship()