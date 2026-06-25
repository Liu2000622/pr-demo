"""VersionController 测试,复刻自 ``VersionControllerTest.java``。"""
from __future__ import annotations


def test_version_returns_plain_text_v1_0(client):
    resp = client.get("/api/version")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert resp.text == "v1.0"
