"""数据库初始化。

对应原项目的 Spring Data JPA 装配(``EntityManagerFactory`` / ``DataSource``)。
使用 SQLAlchemy 2.x,提供全局 ``engine`` / ``SessionLocal`` 与声明式基类 ``Base``。
"""
from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


def _build_engine():
    url = settings.database_url
    # SQLite 内存库需要 StaticPool 才能在多线程/多会话间共享同一内存实例。
    if url.startswith("sqlite"):
        kwargs: dict = {
            "connect_args": {"check_same_thread": False},
            "echo": False,
            "future": True,
        }
        if ":memory:" in url:
            from sqlalchemy.pool import StaticPool

            kwargs["poolclass"] = StaticPool
        return create_engine(url, **kwargs)
    return create_engine(url, echo=False, future=True)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """声明式基类,等价于 JPA 的 ``@Entity`` 公共父类型。"""


def get_db():
    """FastAPI 依赖:每请求提供一个数据库会话并自动关闭。

    对应 Spring 的 ``@Transactional`` / OpenSessionInView 语义。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """建表,对应 Hibernate ``ddl-auto: update``。"""
    # 确保模型已导入,以便 Base.metadata 收集到表定义。
    from app import models  # noqa: F401

    if settings.database_url.startswith("sqlite") and ":memory:" not in settings.database_url:
        db_dir = os.path.dirname(settings.database_url.replace("sqlite:///", ""))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    Base.metadata.create_all(bind=engine)
