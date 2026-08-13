from fastapi import FastAPI
from auth.api import router
from sale import java
from orders import sale
app = FastAPI()

app.include_router(router)
app.include_router(java.router)
app.include_router(sale.router)