from fastapi import FastAPI
from app.presentation.api import item_router
from app.presentation.api import user_router
from app.presentation.api import text_router
from dotenv import load_dotenv

app = FastAPI(title="FastAPI Project with DDD")

# Include routers
app.include_router(item_router.router, prefix="/api/v1", tags=["items"])
app.include_router(user_router.router, prefix="/api/v1", tags=["users"])
app.include_router(text_router.router, prefix="/api/v1", tags=["texts"])

load_dotenv()

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI Project with DDD"}