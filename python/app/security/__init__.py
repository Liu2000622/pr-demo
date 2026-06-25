"""鉴权层聚合。"""
from app.security.auth_filter import ShiroAuthMiddleware
from app.security.realm import authenticate, get_auth_info, get_role
from app.security.session_store import Session, SessionStore, session_store
from app.security.shiro_config import (
    ACTION_ANON,
    ACTION_AUTHC,
    SESSION_COOKIE_NAME,
    filter_chain,
    match_action,
    matches,
)

__all__ = [
    "ShiroAuthMiddleware",
    "authenticate",
    "get_auth_info",
    "get_role",
    "Session",
    "SessionStore",
    "session_store",
    "SESSION_COOKIE_NAME",
    "ACTION_ANON",
    "ACTION_AUTHC",
    "filter_chain",
    "match_action",
    "matches",
]
