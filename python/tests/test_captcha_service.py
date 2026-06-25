"""CaptchaService 单元测试,复刻自 ``CaptchaServiceTest.java``。"""
from __future__ import annotations

import re

from app.services.captcha_service import CAPTCHA_LENGTH, CaptchaService

_TEXT_RE = re.compile(r"[23456789A-Za-z]{6}")


def test_generated_captcha_has_expected_shape():
    service = CaptchaService()
    captcha = service.generate()
    assert captcha.id
    assert len(captcha.text) == CAPTCHA_LENGTH
    assert _TEXT_RE.fullmatch(captcha.text)
    assert captcha.image.startswith("data:image/png;base64,")


def test_verify_accepts_correct_text_case_insensitively():
    service = CaptchaService()
    captcha = service.generate()
    assert service.verify(captcha.id, captcha.text) is True


def test_verify_accepts_lowercased_text():
    service = CaptchaService()
    captcha = service.generate()
    assert service.verify(captcha.id, captcha.text.lower()) is True


def test_verify_rejects_wrong_text():
    service = CaptchaService()
    captcha = service.generate()
    assert service.verify(captcha.id, "WRONG!") is False


def test_verify_rejects_unknown_id():
    service = CaptchaService()
    assert service.verify("does-not-exist", "anything") is False


def test_verify_rejects_null_and_blank_input():
    service = CaptchaService()
    captcha = service.generate()
    assert service.verify(None, captcha.text) is False
    assert service.verify(captcha.id, None) is False
    assert service.verify(captcha.id, "  ") is False


def test_captcha_is_consumed_after_verification():
    service = CaptchaService()
    captcha = service.generate()
    assert service.verify(captcha.id, captcha.text) is True
    # 同一 id 第二次校验必须失败(单次使用)。
    assert service.verify(captcha.id, captcha.text) is False
