"""PasswordService 测试。

包含与 Apache Shiro ``Sha256Hash`` 的算法一致性校验:同一 (password, salt,
1024) 输入,Python 实现与 Java Shiro 产出的十六进制哈希逐位相同。
向量取自真实 Shiro 2.2.1 运行结果。
"""
from __future__ import annotations

import re

from app.services import password_service

_HEX_RE = re.compile(r"[0-9a-f]{64}")


def test_generate_salt_is_hex_and_correct_length():
    salt = password_service.generate_salt()
    # 16 字节 -> 32 个十六进制字符。
    assert len(salt) == 32
    assert re.fullmatch(r"[0-9a-f]{32}", salt)


def test_hash_is_hex_sha256_length():
    h = password_service.hash_password("admin123", password_service.generate_salt())
    assert _HEX_RE.fullmatch(h)


def test_verify_roundtrip():
    salt = password_service.generate_salt()
    h = password_service.hash_password("s3cret", salt)
    assert password_service.verify("s3cret", salt, h) is True
    assert password_service.verify("wrong", salt, h) is False


def test_hash_matches_shiro_vectors():
    """与 Shiro 2.2.1 ``Sha256Hash(pw, salt, 1024).toHex()`` 实算结果一致。"""
    assert (
        password_service.hash_password("admin123", "deadbeefcafebabe")
        == "7772e492e20a7f82f0f26668dd2b4c1601a201ccaa89e89465e3a0c4dc7c7c40"
    )
    assert (
        password_service.hash_password(
            "secret123", "00112233445566778899aabbccddeeff"
        )
        == "516d36931b35d6261cab983541f823bf44329ca0c6e25d2f9325603e87c46d61"
    )
