"""AuthController 的 Python 复刻。

对应原项目 ``controller/AuthController.java``,接口路径、请求体、
响应体与状态码逐条一致。默认种子账号 ``admin`` / ``admin123``。

端点:
- ``GET  /api/captcha``  颁发新验证码(id + base64 图片)
- ``POST /api/login``    用户名 + 密码 + 验证码 登录
- ``POST /api/register`` 注册新用户(用户名 + 密码 + 验证码)
- ``POST /api/logout``   注销当前会话
- ``GET  /api/me``       报告当前(可能匿名)主体(需认证)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import repository as repo
from app.database import get_db
from app.security import SESSION_COOKIE_NAME, authenticate, session_store
from app.services import captcha_service as captcha_module
from app.services import password_service

router = APIRouter(prefix="/api", tags=["auth"])

_USERNAME_MIN = 3
_USERNAME_MAX = 32
_PASSWORD_MIN = 6
_PASSWORD_MAX = 64
_SESSION_MAX_AGE = 30 * 60  # 对应 Java ``addSessionCookie(..., 30 * 60)``


class LoginRequest(BaseModel):
    """对应 Java ``record LoginRequest``。"""

    username: str | None = None
    password: str | None = None
    captchaId: str | None = None
    captcha: str | None = None


class RegisterRequest(BaseModel):
    """对应 Java ``record RegisterRequest``。"""

    username: str | None = None
    password: str | None = None
    captchaId: str | None = None
    captcha: str | None = None


@router.get("/captcha")
def captcha() -> dict:
    """颁发新验证码,返回 ``{captchaId, image}``;明文不返回客户端。"""
    cap = captcha_module.captcha_service.generate()
    return {"captchaId": cap.id, "image": cap.image}


@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> dict:
    # 1) 校验验证码(单次使用)。
    if not captcha_module.captcha_service.verify(payload.captchaId, payload.captcha):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"code": 400, "message": "Invalid or expired captcha"}

    # 2) 认证。
    user = authenticate(db, payload.username or "", payload.password or "")
    if user is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"code": 401, "message": "Invalid username or password"}

    # 3) 创建会话并下发 cookie。
    session = session_store.create(user.username)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session.id,
        max_age=_SESSION_MAX_AGE,
        path="/",
        httponly=True,
    )
    return {"username": user.username, "sessionId": session.id}


@router.post("/register")
def register(
    payload: RegisterRequest, response: Response, db: Session = Depends(get_db)
) -> dict:
    if not captcha_module.captcha_service.verify(payload.captchaId, payload.captcha):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"code": 400, "message": "Invalid or expired captcha"}

    username = (payload.username or "").strip()
    password = payload.password or ""
    if not (_USERNAME_MIN <= len(username) <= _USERNAME_MAX):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "code": 400,
            "message": f"Username must be between {_USERNAME_MIN} and {_USERNAME_MAX} characters",
        }
    if not (_PASSWORD_MIN <= len(password) <= _PASSWORD_MAX):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "code": 400,
            "message": f"Password must be between {_PASSWORD_MIN} and {_PASSWORD_MAX} characters",
        }
    if repo.count_by_username(db, username) > 0:
        response.status_code = status.HTTP_409_CONFLICT
        return {"code": 409, "message": "Username already exists"}

    salt = password_service.generate_salt()
    user = repo.save_user(
        db,
        _build_user(
            username=username,
            salt=salt,
            password=password_service.hash_password(password, salt),
            role="user",
        ),
    )
    response.status_code = status.HTTP_201_CREATED
    return {
        "code": 201,
        "message": "User registered successfully",
        "username": user.username,
    }


@router.post("/logout")
def logout(request: Request, response: Response) -> dict:
    # 尽力注销:无论 cookie/会话是否存在,都清除 cookie(对应 Java best-effort)。
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    session_store.remove(session_id)
    response.set_cookie(SESSION_COOKIE_NAME, "", max_age=0, path="/", httponly=True)
    return {"message": "logged out"}


@router.get("/me")
def me(request: Request) -> dict:
    # 该端点受 authc 保护(见过滤链),到达此处必已认证。
    return {"username": request.state.principal, "authenticated": request.state.authenticated}


# ---- 辅助 ----


def _build_user(*, username: str, salt: str, password: str, role: str):
    from app.models.user import User

    user = User()
    user.username = username
    user.salt = salt
    user.password = password
    user.role = role
    return user
