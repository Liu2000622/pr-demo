"""应用配置。

对应原项目的 ``application.yml``。原 Java 项目生产用 MySQL、测试用 H2;
Python 版默认用 SQLite 以保证开箱即用,并允许通过环境变量切换数据库。
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    """全局配置项(只读)。"""

    #: 服务端口,对应 ``server.port: 8080``。
    app_port: int = int(_env("APP_PORT", "8080"))

    #: 应用名,对应 ``spring.application.name``。
    application_name: str = _env("APP_NAME", "scaffold-app")

    #: 数据库 URL。对应生产 ``jdbc:mysql://...`` / 测试 ``jdbc:h2:mem:...``。
    #: 默认 SQLite 文件库,可改为 ``mysql+pymysql://...`` 等。
    database_url: str = _env("DATABASE_URL", "sqlite:///./data/scaffold.db")

    #: Hibernate ``ddl-auto: update`` 的等价行为:启动时建表。
    create_tables: bool = _env("DDL_AUTO", "update").lower() in {"update", "create", "create-drop"}

    #: 会话超时(秒),对应 Shiro ``SESSION_TIMEOUT_MILLIS = 30 * 60 * 1000``。
    session_timeout_seconds: int = 30 * 60

    #: 验证码 TTL(秒),对应 ``CaptchaService.TTL_MILLIS = 5 * 60 * 1000``。
    captcha_ttl_seconds: int = 5 * 60


settings = Settings()
