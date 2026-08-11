import uuid
from config.database import Base
from sqlalchemy import (
    Column,
    Integer,
    UUID,
    String,
    Boolean,
    Numeric,
    ForeignKey,
)
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
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)

    products: Mapped[list["Product"]] = relationship(back_populates="author" ,cascade='all, delete-orphan')

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