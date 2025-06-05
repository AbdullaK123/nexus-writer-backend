from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.config.settings import app_config


engine = create_async_engine(
    app_config.database_url,
    echo=app_config.debug,
    pool_size=5,
    max_overflow=10
)


async def get_db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session