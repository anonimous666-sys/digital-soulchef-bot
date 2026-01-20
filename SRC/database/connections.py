Денис Слепцов:
"""
Подключение к базе данных и управление сессиями
"""

import asyncio
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import event
from sqlalchemy.engine import Engine

from src.config.settings import settings
from src.database.models import Base

# Создаём асинхронный движок SQLAlchemy
engine = create_async_engine(
    settings.database_url_async,
    echo=settings.is_development,  # Вывод SQL в консоль в режиме разработки
    poolclass=NullPool,  # Используем NullPool для асинхронных операций
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=3600,  # Переподключение каждые час
)

# Создаём фабрику сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Не сбрасывать состояние объектов после коммита
    autocommit=False,
    autoflush=False,
)

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Контекстный менеджер для получения сессии БД.
    
    Использование:
    async with get_db() as session:
        result = await session.execute(query)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """
    Инициализация базы данных (создание таблиц).
    
    Вызывается при старте приложения.
    """
    async with engine.begin() as conn:
        # Создаем все таблицы
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ База данных инициализирована")

async def drop_db():
    """
    Удаление всех таблиц из базы данных.
    
    Только для разработки!
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("🗑️ База данных очищена")

async def health_check() -> bool:
    """
    Проверка работоспособности базы данных.
    
    Returns:
        bool: True если БД доступна, False в противном случае
    """
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False

async def get_database_size() -> Optional[str]:
    """
    Получить размер базы данных.
    
    Returns:
        str: Размер БД в читаемом формате
    """
    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            )
            size = result.scalar()
            return size
    except Exception:
        return None

async def get_table_counts() -> dict:
    """
    Получить количество записей в основных таблицах.
    
    Returns:
        dict: Словарь с количеством записей по таблицам
    """
    from src.database.models import (
        User, Product, Arrival, TTK, Task, AKP, Report, Waste
    )
    
    tables = {
        'users': User,
        'products': Product,
        'arrivals': Arrival,
        'ttk': TTK,
        'tasks': Task,
        'akp': AKP,
        'reports': Report,
        'waste': Waste,
    }
    
    counts = {}
    async with get_db() as session:
        for name, model in tables.items():
            try:
                result = await session.execute(
                    f"SELECT COUNT(*) FROM {model.__tablename__}"
                )
                count = result.scalar()
                counts[name] = count
            except Exception as e:
                counts[name] = f"error: {e}"
    
    return counts

# Настройка пула соединений
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Настройка SQLite для поддержки внешних ключей.
    Только если используется SQLite.
    """

if engine.url.drivername == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Экспорт
all = [
    'engine',
    'AsyncSessionLocal',
    'get_db',
    'init_db',
    'drop_db',
    'health_check',
    'get_database_size',
    'get_table_counts',
]
