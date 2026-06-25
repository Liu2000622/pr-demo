"""验证码服务。

对应原项目 ``service/CaptchaService.java``:
- 6 位字母数字验证码,剔除易混淆字符 ``0/O/1/I/l``。
- 每个验证码由随机 ``id`` 标识,服务端保存明文 + TTL(5 分钟)。
- 验证为**单次使用**:无论对错,一经校验即消费,不可重放。
- 明文永不返回客户端,只返回渲染后的 PNG(base64 data URI)。

存储为进程内字典(对应原 ``ConcurrentHashMap``),单实例足够;
多实例部署应替换为共享缓存(如 Redis)。
"""
from __future__ import annotations

import base64
import io
import secrets
import threading
import time

from PIL import Image, ImageDraw, ImageFont

from app.config import settings

#: 验证码长度,对应 ``CaptchaService.CAPTCHA_LENGTH``。
CAPTCHA_LENGTH = 6

#: 验证码 TTL(秒),对应 ``TTL_MILLIS = 5 * 60 * 1000``。
_TTL_SECONDS = settings.captcha_ttl_seconds

_IMAGE_WIDTH = 160
_IMAGE_HEIGHT = 48

#: 剔除 0/O/1/I/l 等易混淆字符。
_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz"

#: 背景色,对应 Java ``new Color(245, 248, 252)``。
_BACKGROUND = (245, 248, 252)


class Captcha:
    """对应 Java ``record Captcha(String id, String text, String image)``。"""

    __slots__ = ("id", "text", "image")

    def __init__(self, captcha_id: str, text: str, image: str) -> None:
        self.id = captcha_id
        self.text = text
        self.image = image


class _Entry:
    __slots__ = ("text", "expires_at")

    def __init__(self, text: str, expires_at: float) -> None:
        self.text = text
        self.expires_at = expires_at


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """加载粗体字体;退回到 Pillow 默认字体(镜像 Java ``new Font("SansSerif", BOLD, 28)``)。"""
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


class CaptchaService:
    """验证码生成与校验。对应 ``@Component class CaptchaService``。"""

    def __init__(self) -> None:
        self._store: dict[str, _Entry] = {}
        self._lock = threading.Lock()
        self._font = _load_font(28)

    def generate(self) -> Captcha:
        """生成一个新验证码,返回其 id / 明文 / base64 图片。"""
        text = self._random_text()
        captcha_id = self._random_id()
        image = self._render_image(text)
        with self._lock:
            self._store[captcha_id] = _Entry(text, time.time() + _TTL_SECONDS)
            self._cleanup_locked()
        return Captcha(captcha_id, text, image)

    def verify(self, captcha_id: str | None, input_text: str | None) -> bool:
        """校验(并消费)指定 id 的验证码,大小写不敏感。

        对应 Java ``verify``:id / 输入为空或空白即拒绝;条目不存在(或已被消费)
        即拒绝;过期即拒绝;否则消费并返回比较结果。
        """
        if captcha_id is None or input_text is None or input_text.strip() == "":
            return False
        with self._lock:
            entry = self._store.pop(captcha_id, None)  # 单次使用
        if entry is None:
            return False
        if time.time() > entry.expires_at:
            return False
        return entry.text.strip().lower() == input_text.strip().lower()

    # ---- 内部工具 ----

    def _random_text(self) -> str:
        return "".join(secrets.choice(_ALPHABET) for _ in range(CAPTCHA_LENGTH))

    def _random_id(self) -> str:
        # 对应 Java:16 随机字节 -> 小写十六进制(32 字符)。
        return secrets.token_hex(16)

    def _render_image(self, text: str) -> str:
        img = Image.new("RGB", (_IMAGE_WIDTH, _IMAGE_HEIGHT), _BACKGROUND)
        draw = ImageDraw.Draw(img)

        # 干扰线(对应 6 条随机噪声线)。
        for _ in range(6):
            color = (secrets.randbelow(180), secrets.randbelow(180), secrets.randbelow(180))
            x1, y1 = secrets.randbelow(_IMAGE_WIDTH), secrets.randbelow(_IMAGE_HEIGHT)
            x2, y2 = secrets.randbelow(_IMAGE_WIDTH), secrets.randbelow(_IMAGE_HEIGHT)
            draw.line([(x1, y1), (x2, y2)], fill=color, width=1)

        # 字符(粗体、随机颜色、轻微旋转)。
        x = 10
        for ch in text:
            color = (secrets.randbelow(120), secrets.randbelow(120), secrets.randbelow(120))
            char_img = Image.new("RGBA", (_IMAGE_WIDTH, _IMAGE_HEIGHT), (0, 0, 0, 0))
            char_draw = ImageDraw.Draw(char_img)
            char_draw.text((x, 6), ch, font=self._font, fill=color)
            angle = (secrets.randbelow(60) - 30) / 5.0 * 3.0  # 约 ±18°
            rotated = char_img.rotate(angle, expand=False)
            img.paste(rotated, (0, 0), rotated)
            x += 24

        # 颗粒噪声(对应 40 个 1x1 像素点)。
        for _ in range(40):
            color = (secrets.randbelow(200), secrets.randbelow(200), secrets.randbelow(200))
            draw.point(
                (secrets.randbelow(_IMAGE_WIDTH), secrets.randbelow(_IMAGE_HEIGHT)),
                fill=color,
            )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    def _cleanup_locked(self) -> None:
        """廉价清理过期项(对应 Java ``cleanup()``),调用方需持锁。"""
        now = time.time()
        expired = [k for k, v in self._store.items() if now > v.expires_at]
        for k in expired:
            self._store.pop(k, None)


# 模块级单例,等价于 Spring 的 ``@Component`` Bean。
captcha_service = CaptchaService()
