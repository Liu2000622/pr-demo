"""密码服务。

对应原项目 ``service/PasswordService.java``,基于 Apache Shiro 的 ``Sha256Hash``。
- 盐:16 个随机字节,十六进制编码(小写),对应 ``HexFormat.of().formatHex``。
- 哈希:SHA-256,1024 次迭代,十六进制输出。
- 迭代次数 ``ITERATIONS`` 必须与鉴权端校验保持一致(对应 Shiro
  ``HashedCredentialsMatcher.setHashIterations``)。

Shiro ``SimpleHash`` 的算法等价于:
    h0 = sha256(salt_bytes + password_bytes)
    h_i = sha256(h_{i-1})   for i in 1 .. iterations-1
盐只在首轮注入,字符串盐按 UTF-8 解码为字节。最终取十六进制小写。
"""
from __future__ import annotations

import hashlib
import secrets

from app.config import settings

ITERATIONS = 1024
_SALT_BYTES = 16


def generate_salt() -> str:
    """生成 16 字节随机盐,返回小写十六进制串。

    对应 ``PasswordService.generateSalt()``。
    """
    return secrets.token_hex(_SALT_BYTES)


def hash_password(plain_password: str, salt: str) -> str:
    """对明文密码加盐哈希,返回十六进制串。

    对应 ``new Sha256Hash(plainPassword, salt, ITERATIONS).toHex()``。
    """
    h = hashlib.sha256()
    h.update(salt.encode("utf-8"))            # 首轮注入盐(UTF-8 字节)
    h.update(plain_password.encode("utf-8"))  # 再注入明文(UTF-8 字节)
    digest = h.digest()
    for _ in range(1, ITERATIONS):
        digest = hashlib.sha256(digest).digest()
    return digest.hex()


def verify(plain_password: str, salt: str, stored_hash: str) -> bool:
    """校验明文密码与存储哈希是否匹配。

    对应 Shiro ``HashedCredentialsMatcher`` 的比对逻辑(常量时间比较)。
    """
    computed = hash_password(plain_password, salt)
    return secrets.compare_digest(computed, stored_hash or "")
