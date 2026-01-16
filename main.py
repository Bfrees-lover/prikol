from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn

from config import settings
from src.api import router as api_router
from src.models import database

app = FastAPI(
    title=settings.app_name,
    description="Платформа для ставок на спорт с рандомизированными событиями и системой коэффициентов",
    version=settings.app_version
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # Initialize database
    await database.init_db()

@app.on_event("shutdown")
async def shutdown():
    # Close database connections
    await database.close_db()

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Добро пожаловать в платформу Самарин Сережкин - Ставки на спорт"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)