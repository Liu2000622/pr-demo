"""HelloController 的 Python 复刻。

对应原项目 ``controller/HelloController.java``:
- ``GET /api/hello``  -> "Hello, Spring Boot Scaffold is running!"(需认证)
- ``GET /api/ping``   -> "pong"(text/plain,匿名)
- ``GET /api/users``  -> 用户列表 JSON(需认证)
- ``GET /api/version``-> "v1.0"(text/plain,匿名)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app import repository as repo
from app.database import get_db

router = APIRouter(prefix="/api", tags=["hello"])


@router.get("/hello")
def hello() -> str:
    """对应 ``hello()``。"""
    return "Hello, Spring Boot Scaffold is running!"


@router.get("/ping", response_class=Response)
def ping() -> Response:
    """对应 ``ping()``,产出 ``text/plain`` 的 ``pong``。"""
    return Response(content="pong", media_type="text/plain")


@router.get("/users")
def get_users(db: Session = Depends(get_db)) -> list[dict]:
    """对应 ``getUsers()``,返回全部用户(字段与原 JPA 序列化一致)。"""
    return [u.to_dict() for u in repo.find_all_users(db)]


@router.get("/version", response_class=Response)
def version() -> Response:
    """对应 ``version()``,产出 ``text/plain`` 的 ``v1.0``。"""
    return Response(content="v1.0", media_type="text/plain")
