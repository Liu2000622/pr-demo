"""AuthController 集成测试,复刻自 ``AuthControllerTest.java``。

覆盖:匿名端点可访问、受保护端点需认证、验证码门控的登录与注册、
认证后访问、登出失效,以及验证码单次使用语义。
"""
from __future__ import annotations

from app.services.captcha_service import captcha_service

SESSION_COOKIE = "SHIRO_SESSION_ID"


def _clear_cookies(client) -> None:
    """清空 TestClient cookie 罐,保证匿名请求不被前序测试遗留会话污染。"""
    try:
        client.cookies.clear()
    except AttributeError:
        client.cookies = {}


def _set_session(client, sid: str) -> None:
    """在 client 实例上设置会话 cookie(避免 per-request cookies 的弃用警告)。"""
    _clear_cookies(client)
    client.cookies.set(SESSION_COOKIE, sid)


def _captcha():
    """生成一个验证码(走与服务端同一个单例)。"""
    return captcha_service.generate()


def _login(client, username: str, password: str):
    """登录并返回会话 cookie 值(对应 Java ``login`` 辅助方法)。"""
    _clear_cookies(client)
    cap = _captcha()
    resp = client.post(
        "/api/login",
        json={
            "username": username,
            "password": password,
            "captchaId": cap.id,
            "captcha": cap.text,
        },
    )
    assert resp.status_code == 200, resp.text
    sid = resp.cookies.get(SESSION_COOKIE)
    assert sid, "登录未下发会话 cookie"
    return sid


# ---- 匿名端点 ----


def test_anonymous_endpoints_are_accessible_without_auth(client):
    _clear_cookies(client)
    assert client.get("/api/version").text == "v1.0"
    assert client.get("/api/ping").text == "pong"


def test_captcha_endpoint_returns_image(client):
    _clear_cookies(client)
    resp = client.get("/api/captcha")
    assert resp.status_code == 200
    body = resp.json()
    assert body["captchaId"]
    assert body["image"].startswith("data:image/png;base64,")


# ---- 受保护端点 ----


def test_protected_endpoints_return_401_without_auth(client):
    _clear_cookies(client)
    assert client.get("/api/users").status_code == 401
    assert client.get("/api/hello").status_code == 401
    assert client.get("/api/me").status_code == 401


# ---- 登录 ----


def test_login_without_captcha_is_rejected(client):
    _clear_cookies(client)
    resp = client.post(
        "/api/login", json={"username": "admin", "password": "admin123"}
    )
    assert resp.status_code == 400


def test_login_with_wrong_captcha_is_rejected(client):
    _clear_cookies(client)
    cap = _captcha()
    resp = client.post(
        "/api/login",
        json={
            "username": "admin",
            "password": "admin123",
            "captchaId": cap.id,
            "captcha": "WRONG",
        },
    )
    assert resp.status_code == 400


def test_captcha_is_single_use(client):
    _clear_cookies(client)
    cap = _captcha()
    # 首次使用(密码错,但验证码正确)消费掉验证码 -> 401。
    resp1 = client.post(
        "/api/login",
        json={
            "username": "admin",
            "password": "wrong",
            "captchaId": cap.id,
            "captcha": cap.text,
        },
    )
    assert resp1.status_code == 401
    # 同一验证码再次使用必须因验证码失效返回 400,而非 401。
    resp2 = client.post(
        "/api/login",
        json={
            "username": "admin",
            "password": "admin123",
            "captchaId": cap.id,
            "captcha": cap.text,
        },
    )
    assert resp2.status_code == 400


def test_login_with_invalid_credentials_returns_401(client):
    _clear_cookies(client)
    cap = _captcha()
    resp = client.post(
        "/api/login",
        json={
            "username": "admin",
            "password": "wrong",
            "captchaId": cap.id,
            "captcha": cap.text,
        },
    )
    assert resp.status_code == 401


def test_login_then_access_protected_endpoints(client):
    _clear_cookies(client)
    sid = _login(client, "admin", "admin123")
    _set_session(client, sid)

    assert client.get("/api/users").status_code == 200
    assert client.get("/api/hello").status_code == 200
    me = client.get("/api/me")
    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert me.json()["authenticated"] is True
    _clear_cookies(client)


def test_logout_invalidates_session(client):
    _clear_cookies(client)
    sid = _login(client, "admin", "admin123")
    _set_session(client, sid)

    resp = client.post("/api/logout")
    assert resp.status_code == 200

    # 旧会话 id 不再授权访问。
    _set_session(client, sid)
    assert client.get("/api/users").status_code == 401
    _clear_cookies(client)


# ---- 注册 ----


def test_register_creates_loginable_user(client):
    _clear_cookies(client)
    import time

    username = f"tester{time.time_ns()}"
    cap = _captcha()
    resp = client.post(
        "/api/register",
        json={
            "username": username,
            "password": "secret123",
            "captchaId": cap.id,
            "captcha": cap.text,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["username"] == username

    # 新注册用户可登录。
    sid = _login(client, username, "secret123")
    _set_session(client, sid)
    me = client.get("/api/me")
    assert me.status_code == 200
    assert me.json()["username"] == username
    assert me.json()["authenticated"] is True
    _clear_cookies(client)


def test_register_rejects_duplicate_username(client):
    _clear_cookies(client)
    cap = _captcha()
    resp = client.post(
        "/api/register",
        json={
            "username": "admin",
            "password": "secret123",
            "captchaId": cap.id,
            "captcha": cap.text,
        },
    )
    assert resp.status_code == 409


def test_register_rejects_short_password(client):
    _clear_cookies(client)
    cap = _captcha()
    resp = client.post(
        "/api/register",
        json={
            "username": "shortuser",
            "password": "123",
            "captchaId": cap.id,
            "captcha": cap.text,
        },
    )
    assert resp.status_code == 400
