"""数据初始化。

对应原项目 ``config/DataInitializer.java`` 的 ``CommandLineRunner``:
启动时种子默认管理员 ``admin`` / ``admin123``,并具备"幂等 + 自愈"逻辑——
共享库可能因多次启动累积重复 ``admin`` 行,先合并去重为单条,再重置其
密码/盐/邮箱/角色,确保默认账号始终可用;若无则新建。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app import repository as repo
from app.services import password_service

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_EMAIL = "admin@example.com"
ADMIN_ROLE = "admin"


def init_data(db: Session) -> None:
    """启动时执行,等价于 ``initData`` 的 ``CommandLineRunner``。"""
    existing = repo.find_all_by_username(db, ADMIN_USERNAME)
    if existing:
        keep = existing[0]
        # 合并重复行:保留首条,删除其余(对应 subList(1, size) 删除)。
        for dup in existing[1:]:
            repo.delete_user(db, dup)
        # 重置密码/盐/邮箱/角色,保证默认 admin 永远可用。
        salt = password_service.generate_salt()
        keep.salt = salt
        keep.password = password_service.hash_password(ADMIN_PASSWORD, salt)
        keep.email = ADMIN_EMAIL
        keep.role = ADMIN_ROLE
        repo.save_user(db, keep)
        return

    # 无则新建。
    salt = password_service.generate_salt()
    repo.save_user(
        db,
        _build_admin(salt, password_service.hash_password(ADMIN_PASSWORD, salt)),
    )


def _build_admin(salt: str, password_hash: str):
    from app.models.user import User

    user = User()
    user.username = ADMIN_USERNAME
    user.email = ADMIN_EMAIL
    user.salt = salt
    user.password = password_hash
    user.role = ADMIN_ROLE
    return user
