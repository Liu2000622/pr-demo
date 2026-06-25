"""用户实体。

对应原项目 ``entity/User.java``:字段、列名、含义完全一致。
- ``password``:加盐 SHA-256 哈希的十六进制串(1024 次迭代)。
- ``salt``:每用户随机盐(16 字节的十六进制串)。
- ``role``:角色,用于鉴权(对应 Shiro 授权)。
"""
from __future__ import annotations

from sqlalchemy import BigInteger, Column, Integer, String

from app.database import Base


class User(Base):
    """对应 JPA ``@Entity @Table(name = "users")`` 的 ``User``。"""

    __tablename__ = "users"

    #: 主键,自增,对应 ``@Id @GeneratedValue(strategy = IDENTITY) Long id``。
    #: 在 SQLite 上退化为 ``INTEGER PRIMARY KEY``(方能自增),其它库仍为 BIGINT。
    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    #: 用户名。
    username = Column(String(64), nullable=True)

    #: 邮箱。
    email = Column(String(128), nullable=True)

    #: 加盐 SHA-256 哈希(十六进制)。
    password = Column(String(128), nullable=True)

    #: 每用户盐(十六进制)。
    salt = Column(String(64), nullable=True)

    #: 角色。
    role = Column(String(32), nullable=True)

    def to_dict(self) -> dict:
        """序列化为字典,字段顺序与原 JPA 序列化的 JSON 一致。

        ``GET /api/users`` 直接返回该结构(与原项目行为一致,包含 password/salt)。
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "salt": self.salt,
            "role": self.role,
        }

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"User(id={self.id!r}, username={self.username!r}, role={self.role!r})"
