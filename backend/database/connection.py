from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
import redis
from backend.config import get_settings

settings = get_settings()

# PostgreSQL
engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis
redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5
)


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI para sessão do banco"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_redis() -> redis.Redis:
    """Retorna cliente Redis"""
    return redis_client


def init_db():
    """Inicializa o banco de dados"""
    Base.metadata.create_all(bind=engine)
