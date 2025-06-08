# src/shared/infrastructure/database/connection.py
"""Database connection management - Lambda optimized."""

from typing import AsyncGenerator
import structlog
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

logger = structlog.get_logger()

# Global variables - mantidos durante vida do container Lambda
async_engine = None
async_session_factory = None

class Base(DeclarativeBase):
    """Base class for all database models."""
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s", 
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )

async def init_db(database_url: str) -> None:
    """Initialize database connections - chamado apenas uma vez por container."""
    global async_engine, async_session_factory
    
    if async_engine is not None:
        logger.info("Database already initialized, skipping...")
        return
    
    # Convert PostgreSQL URL for async
    async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    # ✅ Configuração otimizada para Lambda
    async_engine = create_async_engine(
        async_url,
        echo=False,
        # ✅ Pool pequeno para Lambda
        pool_size=1,           # 1 conexão por container Lambda
        max_overflow=0,        # Sem overflow - controle preciso
        pool_timeout=30,       # Timeout para pegar conexão
        pool_recycle=300,      # Reciclar conexão a cada 5min
        pool_pre_ping=True,    # Verificar se conexão está viva
        # ✅ Configurações adicionais para Lambda
        connect_args={
            "server_settings": {
                "application_name": "lambda_function",
            }
        }
    )
    
    async_session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    logger.info("Database connections initialized for Lambda")

async def close_db() -> None:
    """
    ✅ Close database connections - APENAS no shutdown do container.
    NÃO chamar a cada operação!
    """
    global async_engine, async_session_factory
    
    if async_engine:
        await async_engine.dispose()
        async_engine = None
        async_session_factory = None
        logger.info("Database connections closed")

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    if not async_session_factory:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        # ✅ Session é fechada automaticamente pelo 'async with'