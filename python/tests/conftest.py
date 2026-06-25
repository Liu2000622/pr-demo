"""pytest 公共夹具。

对应原项目测试侧的 ``test/resources/application.yml``:使用内存 SQLite,
无需外部 MySQL/H2。必须在导入任何 ``app`` 模块之前设置 ``DATABASE_URL``，
以保证模块级 ``engine`` 指向内存库。
"""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    """启动应用(触发 lifespan:建表 + 种子 admin)并返回 TestClient。"""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db():
    """每测试一个数据库会话。"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
