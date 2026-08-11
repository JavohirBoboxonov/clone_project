from fastapi import FastAPI
from auth.api import router
from sale import java
app = FastAPI()

app.include_router(router)
app.include_router(java.router)