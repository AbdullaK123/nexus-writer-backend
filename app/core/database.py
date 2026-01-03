from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.config.settings import app_config
from sqlmodel import create_engine, Session


engine = create_async_engine(
    app_config.database_url,
    echo=app_config.debug,
    pool_size=15,
    max_overflow=20
)

sync_engine = create_engine(
    app_config.database_sync_url,
    echo=app_config.debug,
    pool_size=5,
    max_overflow=10
)


async def get_db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

def get_sync_db():
    with Session(sync_engine) as session:
        yield session