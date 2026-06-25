"""用户仓储。

对应原项目 ``repository/UserRepository.java``(Spring Data JPA 接口)。
这里以一组函数实现等价查询;刻意保留 ``find_all_by_username``(返回列表)
而非 ``find_one``,以复刻原项目"避免 NonUniqueResultException / 共享库重复行"
的自愈逻辑(见 ``DataInitializer`` 与 ``JpaRealm``)。
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def find_by_username(db: Session, username: str) -> User | None:
    """对应 ``Optional<User> findByUsername(String)``。"""
    return db.execute(
        select(User).where(User.username == username)
    ).scalars().first()


def find_all_by_username(db: Session, username: str) -> list[User]:
    """对应 ``List<User> findAllByUsername(String)``。

    返回列表而非单条,避免共享 MySQL 中历史重复行在登录时抛
    ``NonUniqueResultException``(与原 ``JpaRealm`` 行为一致)。
    """
    return list(
        db.execute(select(User).where(User.username == username)).scalars().all()
    )


def count_by_username(db: Session, username: str) -> int:
    """对应 ``long countByUsername(String)``。"""
    from sqlalchemy import func

    return int(
        db.execute(
            select(func.count()).select_from(User).where(User.username == username)
        ).scalar_one()
    )


def find_all(db: Session) -> list[User]:
    """对应 ``JpaRepository.findAll()``。"""
    return list(db.execute(select(User)).scalars().all())


def save(db: Session, user: User) -> User:
    """对应 ``JpaRepository.save()``:持久化并刷新以拿到自增主键。"""
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete(db: Session, user: User) -> None:
    """对应 ``JpaRepository.delete()``。"""
    db.delete(user)
    db.commit()
