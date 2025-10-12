from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.config import settings

engine = create_async_engine(settings.postgres_dsn.unicode_string())
SessionFactory = async_sessionmaker(engine, expire_on_commit=False, autocommit=False)
