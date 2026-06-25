# Spring Boot Scaffold — Python 版

本项目是 `scaffold-app`(Spring Boot 3 + Apache Shiro + JPA 脚手架)的 Python 复刻版本,
使用 **FastAPI + SQLAlchemy + Pillow** 实现,业务逻辑、接口路径、请求/响应结构与原 Java 项目保持一致。

## 模块对照表

| 原项目 (Java / Spring Boot) | 本项目 (Python) |
| --- | --- |
| `ScaffoldApplication` | `app/main.py` |
| `application.yml` | `app/config.py` |
| JPA / H2 / MySQL | `app/database.py` + SQLAlchemy (默认 SQLite) |
| `entity.User` | `app/models/user.py` |
| `UserRepository` | `app/repository/user_repository.py` |
| `service.PasswordService` (Shiro Sha256Hash, 1024 迭代) | `app/services/password_service.py` |
| `service.CaptchaService` (6 位字母数字, PNG base64, 单次使用) | `app/services/captcha_service.py` |
| `security.JpaRealm` / `ShiroAuthFilter` / `ShiroConfig` | `app/security/*` |
| `controller.AuthController` | `app/controllers/auth_controller.py` |
| `controller.HelloController` | `app/controllers/hello_controller.py` |
| `config.DataInitializer` | `app/data_initializer.py` |
| `static/*.html` | `app/static/*.html`(原样复用) |

## 运行

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

默认账号:`admin` / `admin123`(启动时自动种子,且具备与原项目相同的"自愈去重"逻辑)。

## 测试

```bash
pytest -q
```

测试复刻自原项目的 JUnit 用例(CaptchaServiceTest / AuthControllerTest / VersionControllerTest),
并补充了密码哈希算法与 Shiro 一致性的校验。

## 配置

通过环境变量覆盖(见 `app/config.py`):

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_PORT` | `8080` | 服务端口(与 Java `server.port` 一致) |
| `DATABASE_URL` | `sqlite:///./data/scaffold.db` | 数据库 URL;测试用 `sqlite:///:memory:` |

> 原 Java 项目生产用 MySQL、测试用 H2;Python 版默认用 SQLite 以保证开箱即用,
> 亦可通过 `DATABASE_URL` 切换到 MySQL 等任意 SQLAlchemy 支持的数据库。
