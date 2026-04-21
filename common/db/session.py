from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from common.db.config import PostgresConfig

# Initialize Postgres configuration
pg_config = PostgresConfig()

engine = create_async_engine(
    pg_config.url,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncSession:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        yield session
