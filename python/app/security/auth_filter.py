"""认证过滤器(中间件)。

对应原项目 ``security/ShiroAuthFilter.java``:Jakarta 过滤器将 Shiro 认证核心
接入 Spring Boot 3。这里用 Starlette 中间件实现等价职责——
按 cookie 中的会话 id 还原主体,并按过滤链(anon/authc)放行或拒绝。

- ``anon``:直接放行;
- ``authc``:未认证则返回 401 JSON,与 Java ``writeUnauthorized`` 完全一致。
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.security.session_store import session_store
from app.security.shiro_config import ACTION_AUTHC, match_action

#: 未认证时的响应体,对应 Java ``writeUnauthorized``。
_UNAUTHORIZED_BODY = {"code": 401, "message": "Unauthorized: authentication required"}


class ShiroAuthMiddleware(BaseHTTPMiddleware):
    """等价于 ``ShiroAuthFilter`` 的认证过滤中间件。"""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # 静态资源/favicon 等无需鉴权,直接放行(原项目由 Spring 静态资源处理)。
        if path.startswith("/favicon") or path.startswith("/static/"):
            return await call_next(request)

        session_id = _read_session_cookie(request)
        session = session_store.get(session_id)
        principal = session.principal if session else None
        authenticated = session is not None

        # 绑定到 request.state,等价于 Shiro ``ThreadContext.bind(subject)``。
        request.state.principal = principal
        request.state.authenticated = authenticated
        request.state.session_id = session.id if session else None

        action = match_action(path)
        if action == ACTION_AUTHC and not authenticated:
            return JSONResponse(_UNAUTHORIZED_BODY, status_code=401)
        return await call_next(request)


def _read_session_cookie(request: Request) -> str | None:
    """读取 ``SHIRO_SESSION_ID`` cookie,对应 ``readSessionCookie``。"""
    return request.cookies.get("SHIRO_SESSION_ID")
