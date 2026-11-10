from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


import sys
if "pytest" in sys.modules:
    engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)
else:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_async_db():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
