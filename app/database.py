from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# The engine is the connection pool — created once at startup
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",  # logs SQL in dev, silent in prod
    pool_size=10,
    max_overflow=20,
)

# Session factory — call this to get a DB session
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # prevents "detached instance" errors after commit
)


class Base(DeclarativeBase):
    """All SQLAlchemy models inherit from this."""
    pass


async def get_db():
    """
    FastAPI dependency. Yields a session and guarantees it's closed
    after the request, even if an exception is raised.
    """
    async with AsyncSessionLocal() as session:
        yield session