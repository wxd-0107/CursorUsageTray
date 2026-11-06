"""Fetch current billing period usage from Cursor dashboard API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

USAGE_URL = (
    "https://api2.cursor.sh/aiserver.v1.DashboardService/GetCurrentPeriodUsage"
)

DEFAULT_TIMEOUT = 12.0


@dataclass(frozen=True)
class PlanUsageView:
    auto_used_pct: float | None
    api_used_pct: float | None
    total_used_pct: float | None
    remaining_cents: int | None
    limit_cents: int | None
    display_message: str | None
    auto_message: str | None
    api_message: str | None
    billing_cycle_start_ms: int | None
    billing_cycle_end_ms: int | None

    @property
    def auto_remaining_pct(self) -> float | None:
        if self.auto_used_pct is None:
            return None
        return max(0.0, min(100.0, 100.0 - self.auto_used_pct))

    @property
    def api_remaining_pct(self) -> float | None:
        if self.api_used_pct is None:
            return None
        return max(0.0, min(100.0, 100.0 - self.api_used_pct))

    @property
    def primary_used_pct(self) -> float | None:
        """Best-effort overall used % for display (prefers totalPercentUsed)."""
        if self.total_used_pct is not None:
            return max(0.0, min(100.0, float(self.total_used_pct)))
        parts = [v for v in (self.auto_used_pct, self.api_used_pct) if v is not None]
        if not parts:
            return None
        return max(0.0, min(100.0, max(float(v) for v in parts)))


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_usage_payload(data: dict[str, Any]) -> PlanUsageView:
    plan = data.get("planUsage") or {}
    if not isinstance(plan, dict):
        plan = {}

    return PlanUsageView(
        auto_used_pct=_as_float(plan.get("autoPercentUsed")),
        api_used_pct=_as_float(plan.get("apiPercentUsed")),
        total_used_pct=_as_float(plan.get("totalPercentUsed")),
        remaining_cents=_as_int(plan.get("remaining")),
        limit_cents=_as_int(plan.get("limit")),
        display_message=_as_str(data.get("displayMessage")),
        auto_message=_as_str(data.get("autoModelSelectedDisplayMessage")),
        api_message=_as_str(data.get("namedModelSelectedDisplayMessage")),
        billing_cycle_start_ms=_as_int(data.get("billingCycleStart")),
        billing_cycle_end_ms=_as_int(data.get("billingCycleEnd")),
    )


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def fetch_current_usage(access_token: str) -> PlanUsageView:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Connect-Protocol-Version": "1",
    }
    try:
        resp = requests.post(
            USAGE_URL,
            headers=headers,
            json={},
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"网络请求失败: {exc}") from exc

    if resp.status_code == 401:
        raise RuntimeError("登录已过期，请重新打开 Cursor 或执行 agent login")
    if not resp.ok:
        snippet = (resp.text or "")[:200]
        raise RuntimeError(f"API 错误 HTTP {resp.status_code}: {snippet}")

    try:
        payload = resp.json()
    except ValueError as exc:
        raise RuntimeError("API 返回非 JSON 响应") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("API 响应格式异常")

    return _parse_usage_payload(payload)


def format_percent_value(pct: float) -> str:
    """Format used % with up to one decimal (omit .0)."""
    clamped = max(0.0, min(100.0, float(pct)))
    rounded = round(clamped, 1)
    if abs(rounded - round(rounded)) < 1e-9:
        return str(int(round(rounded)))
    return f"{rounded:.1f}"


def format_used_display(usage: PlanUsageView) -> str:
    pct = usage.primary_used_pct
    if pct is None:
        return "已使用：—"
    return f"已使用：{format_percent_value(pct)}%"


def format_taskbar_text(usage: PlanUsageView) -> str:
    return format_used_display(usage)


def format_tray_title(usage: PlanUsageView) -> str:
    pct = usage.primary_used_pct
    if pct is not None:
        return f"Cursor | 已使用 {format_percent_value(pct)}%"
    if usage.display_message:
        return "Cursor | " + usage.display_message[:60]
    return "Cursor 用量"


def format_tooltip(usage: PlanUsageView) -> str:
    lines: list[str] = []
    if usage.display_message:
        lines.append(usage.display_message)
    if usage.auto_message:
        lines.append(usage.auto_message)
    elif usage.auto_used_pct is not None:
        lines.append(f"Auto/Composer 已用 {usage.auto_used_pct:.1f}%")
    if usage.api_message:
        lines.append(usage.api_message)
    elif usage.api_used_pct is not None:
        lines.append(f"API 模型已用 {usage.api_used_pct:.1f}%")
    if usage.remaining_cents is not None and usage.limit_cents:
        rem_usd = usage.remaining_cents / 100.0
        limit_usd = usage.limit_cents / 100.0
        lines.append(f"套餐额度约 ${rem_usd:.2f} / ${limit_usd:.2f} 剩余")
    if not lines:
        lines.append("已刷新用量（无详细字段）")
    lines.append("左键或菜单「刷新」更新")
    return "\n".join(lines)
