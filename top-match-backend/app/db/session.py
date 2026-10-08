from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    # DB errors must not echo bound values (resume text, emails) into logs.
    hide_parameters=True,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
