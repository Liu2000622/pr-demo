"""会话存储。

对应原项目 Shiro 的 ``DefaultSessionManager`` + ``MemorySessionDAO``:
进程内字典按会话 id 保存会话,带全局超时(30 分钟)。
登录时创建会话,登出时移除;每次请求按 cookie 中的会话 id 还原主体。
"""
from __future__ import annotations

import secrets
import threading
import time

from app.config import settings


class Session:
    """对应 Shiro ``Session``:保存主体(用户名)与过期时间。"""

    __slots__ = ("id", "principal", "expires_at")

    def __init__(self, session_id: str, principal: str, expires_at: float) -> None:
        self.id = session_id
        self.principal = principal
        self.expires_at = expires_at

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class SessionStore:
    """进程内会话存储,对应 ``MemorySessionDAO``。"""

    def __init__(self, timeout_seconds: int = settings.session_timeout_seconds) -> None:
        self._timeout = timeout_seconds
        self._store: dict[str, Session] = {}
        self._lock = threading.Lock()

    def create(self, principal: str) -> Session:
        """创建新会话并返回。对应登录成功后 ``subject.getSession()``。"""
        session_id = secrets.token_hex(16)
        session = Session(session_id, principal, time.time() + self._timeout)
        with self._lock:
            self._store[session_id] = session
        return session

    def get(self, session_id: str | None) -> Session | None:
        """按 id 取会话;不存在或已过期则返回 None(并顺手清理过期项)。"""
        if not session_id:
            return None
        with self._lock:
            session = self._store.get(session_id)
            if session is None:
                return None
            if session.is_expired:
                self._store.pop(session_id, None)
                return None
            return session

    def remove(self, session_id: str | None) -> None:
        """移除会话。对应登出 ``subject.logout()``。"""
        if not session_id:
            return
        with self._lock:
            self._store.pop(session_id, None)


# 模块级单例,等价于 Spring Bean ``sessionManager``。
session_store = SessionStore()
