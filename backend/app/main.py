
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .db.init_db import create_tables
from .api.chat import router as chat_router
from .api.properties import router as properties_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(
    title="Vacation Rental AI Assistant",
    description="AI-powered assistant for vacation rental websites",
    version="1.0.0",
    lifespan=lifespan,
)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Vacation Rental AI Assistant backend is running",
    }

app.include_router(chat_router)
app.include_router(properties_router)