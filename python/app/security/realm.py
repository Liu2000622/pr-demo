"""认证 Realm。

对应原项目 ``security/JpaRealm.java`` + ``HashedCredentialsMatcher``:
按用户名查到用户(取列表首条以规避重复行),再用 ``PasswordService``
以同样的盐与迭代次数重算提交密码的哈希,与库中哈希常量时间比较。
"""
from __future__ import annotations

from sqlalchemy.orm import Session as DBSession

from app import repository as repo
from app.models.user import User
from app.services import password_service


def get_auth_info(db: DBSession, username: str) -> User | None:
    """对应 ``doGetAuthenticationInfo``:按用户名取用户(列表首条)。"""
    users = repo.find_all_by_username(db, username)
    return users[0] if users else None


def authenticate(db: DBSession, username: str, password: str) -> User | None:
    """校验用户名/密码,成功返回用户,失败返回 None。

    对应 Shiro 登录流程:取认证信息 -> ``CredentialsMatcher`` 比对哈希。
    """
    user = get_auth_info(db, username)
    if user is None:
        return None
    if not password_service.verify(password, user.salt or "", user.password or ""):
        return None
    return user


def get_role(db: DBSession, username: str) -> str | None:
    """对应 ``doGetAuthorizationInfo``:返回用户角色。"""
    user = get_auth_info(db, username)
    return user.role if user else None
