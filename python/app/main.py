"""应用入口。

对应原项目 ``ScaffoldApplication.java``:创建并装配整个应用。
- 建表(Hibernate ``ddl-auto: update``);
- 注册认证过滤中间件(Shiro ``ShiroAuthFilter``);
- 挂载控制器路由(``AuthController`` / ``HelloController``);
- 挂载静态页面(``static/*.html``);
- 启动时种子默认 admin(``DataInitializer``)。
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.responses import JSONResponse

from app.config import settings
from app.controllers import auth_controller, hello_controller
from app.data_initializer import init_data
from app.database import SessionLocal, init_db
from app.security import ShiroAuthMiddleware

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """对应 Spring 启动:建表 + 种子数据。"""
    init_db()
    db = SessionLocal()
    try:
        init_data(db)
    finally:
        db.close()
    yield


app = FastAPI(title="springboot-scaffold (Python)", version="1.0.0", lifespan=_lifespan)

# 认证过滤中间件,等价于注册 ``ShiroAuthFilter``。
app.add_middleware(ShiroAuthMiddleware)

# ---- 控制器路由 ----
app.include_router(auth_controller.router)
app.include_router(hello_controller.router)


# ---- 静态页面 ----
# 显式映射 /login.html /register.html /index.html / ,与 Java 静态资源行为一致
# (这些路径在过滤链中均为 anon)。
@app.get("/login.html", include_in_schema=False)
def _login_page() -> FileResponse:
    return FileResponse(os.path.join(_STATIC_DIR, "login.html"))


@app.get("/register.html", include_in_schema=False)
def _register_page() -> FileResponse:
    return FileResponse(os.path.join(_STATIC_DIR, "register.html"))


@app.get("/index.html", include_in_schema=False)
def _index_page() -> FileResponse:
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"))


@app.get("/", include_in_schema=False)
def _root() -> FileResponse:
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"))


# 兜底错误页,对应 Spring 的 /error(anon)。
@app.get("/error", include_in_schema=False)
def _error() -> JSONResponse:
    return JSONResponse({"code": 500, "message": "error"}, status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.app_port)
