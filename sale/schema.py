from pydantic import BaseModel, model_validator

import uuid

class ProductBase(BaseModel):
    product_id: int
    user_id: str
    title: str
    description: str
    pictures: str = None
    price: float

class ProductResponseSchema(ProductBase):
    product_id: int
    title: str
    user_id: uuid.UUID
    description: str
    pictures: str = None
    stock: int
    price: float
    total: float = 0

    @model_validator(mode='after')
    def calculate(self):
        self.total = self.stock * self.price
        return self.total
    class Config:
        from_attributes = True