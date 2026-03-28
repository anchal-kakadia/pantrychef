from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code here runs ONCE at startup
    print(f"Starting PantryChef [{settings.app_env}]")
    yield
    # Code here runs ONCE at shutdown
    await engine.dispose()
    print("DB connections closed")


app = FastAPI(
    title="PantryChef API",
    version="0.1.0",
    # In production, hide the docs from the public internet
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Load balancer / uptime monitor hits this. Must stay fast and simple."""
    return {"status": "ok"}