"""Shiro 过滤链配置。

对应原项目 ``config/ShiroConfig.java`` 的 ``filterChain()``:
显式列出每个端点的匿名(anon)/ 需认证(authc)规则,顺序匹配,首条命中生效,
未命中项默认 ``authc``。保证没有任何端点被意外漏配。

静态页面(/login.html 等)设为 anon,页面自身通过 /api/me 判断登录态。
"""
from __future__ import annotations

from collections import OrderedDict

#: Cookie 名,对应 ``ShiroAuthFilter.SESSION_COOKIE_NAME``。
SESSION_COOKIE_NAME = "SHIRO_SESSION_ID"

ACTION_ANON = "anon"
ACTION_AUTHC = "authc"


def filter_chain() -> "OrderedDict[str, str]":
    """返回有序过滤链(模式 -> 动作),与 Java ``filterChain()`` 逐条一致。"""
    chain: "OrderedDict[str, str]" = OrderedDict()
    chain["/api/login"] = ACTION_ANON
    chain["/api/logout"] = ACTION_ANON
    chain["/api/register"] = ACTION_ANON
    chain["/api/captcha"] = ACTION_ANON
    chain["/api/version"] = ACTION_ANON
    chain["/api/ping"] = ACTION_ANON
    chain["/login.html"] = ACTION_ANON
    chain["/register.html"] = ACTION_ANON
    chain["/index.html"] = ACTION_ANON
    chain["/"] = ACTION_ANON
    chain["/error"] = ACTION_ANON
    chain["/**"] = ACTION_AUTHC
    return chain


def matches(pattern: str, path: str) -> bool:
    """Ant 风格匹配,对应 ``ShiroAuthFilter.matches``。

    支持 ``/**``(任意深度)、``/*``(单段)与精确匹配。
    """
    if pattern == "/**":
        return True
    if pattern.endswith("/**"):
        prefix = pattern[: -len("/**")]
        return path.startswith(prefix)
    if pattern.endswith("/*"):
        prefix = pattern[: -len("/*")]
        if not path.startswith(prefix):
            return False
        remainder = path[len(prefix):]
        return "/" not in remainder
    return pattern == path


def match_action(path: str) -> str:
    """返回路径命中的动作;未命中则安全默认为 ``authc``。"""
    for pattern, action in filter_chain().items():
        if matches(pattern, path):
            return action
    return ACTION_AUTHC
