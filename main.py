"""Cursor usage monitor — floating badge + Windows system tray."""

from __future__ import annotations

import ctypes
import sys
import threading
import tkinter as tk
import webbrowser
from datetime import datetime, timedelta

import pystray
from PIL import Image

from cursor_api import fetch_current_usage, format_tooltip, format_tray_title
from cursor_auth import get_access_token
from float_window import FloatWindow
from tray_icon import build_tray_icon, icon_label

DASHBOARD_URL = "https://cursor.com/dashboard"
# NOTIFYICONDATAW.szTip — 含结尾 \0，最多 128 个 WCHAR
WIN_TRAY_TIP_MAX = 127
# 工作日 8:00–22:00，每 30 分钟
AUTO_START_HOUR = 8
AUTO_END_HOUR = 22
AUTO_INTERVAL = timedelta(minutes=30)


def in_auto_window(now: datetime) -> bool:
    if now.weekday() >= 5:
        return False
    start = now.replace(hour=AUTO_START_HOUR, minute=0, second=0, microsecond=0)
    end = now.replace(hour=AUTO_END_HOUR, minute=0, second=0, microsecond=0)
    return start <= now <= end


def next_auto_slot(now: datetime) -> datetime:
    """Next weekday :00/:30 slot in 8:00–22:00, strictly after `now`."""
    cursor = now.replace(second=0, microsecond=0)
    if cursor.minute < 30:
        cursor = cursor.replace(minute=30)
    else:
        cursor = cursor.replace(minute=0) + timedelta(hours=1)
    if cursor <= now:
        cursor += AUTO_INTERVAL
    for _ in range(48 * 14):
        if (
            cursor.weekday() < 5
            and AUTO_START_HOUR <= cursor.hour <= AUTO_END_HOUR
            and cursor.minute in (0, 30)
            and not (cursor.hour == AUTO_END_HOUR and cursor.minute > 0)
        ):
            return cursor
        cursor += AUTO_INTERVAL
    return now + AUTO_INTERVAL


class TrayApp:
    def __init__(self) -> None:
        self._click_through = False
        self._refresh_lock = threading.Lock()
        self._busy = False
        self._stop = threading.Event()
        self._root = tk.Tk()
        self._root.withdraw()
        self._float = FloatWindow(
            self._root,
            on_right_click=self._show_context_menu,
            on_close=self._quit_from_window,
        )
        self._icon = pystray.Icon(
            "cursor_usage_tray",
            build_tray_icon("--", dim=True),
            "Cursor 用量 — 加载中",
            menu=pystray.Menu(
                pystray.MenuItem("刷新用量", self._on_refresh, default=True),
                pystray.MenuItem("打开 Dashboard", self._on_open_dashboard),
                pystray.MenuItem(
                    "穿透模式",
                    self._on_toggle_click_through,
                    checked=lambda _item: self._click_through,
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", self._on_quit),
            ),
        )
        self._ctx = tk.Menu(self._root, tearoff=0)
        self._ctx.add_command(
            label="刷新用量",
            command=lambda: self._run_menu_action(self._refresh_async),
        )
        self._ctx.add_command(
            label="打开 Dashboard",
            command=lambda: self._run_menu_action(self._open_dashboard),
        )
        self._ctx.add_separator()
        self._ctx.add_command(
            label="退出",
            command=lambda: self._run_menu_action(self._quit_from_window),
        )

    def run(self) -> None:
        if in_auto_window(datetime.now()):
            threading.Thread(target=self._refresh_async, daemon=True).start()
        else:
            waiting = "Cursor 用量 — 非自动刷新时段（工作日 8:00–22:00）"
            self._icon.title = waiting
            self._float.set_status("--", dim=True, tooltip=waiting)
        threading.Thread(target=self._schedule_loop, daemon=True).start()
        threading.Thread(target=self._icon.run, daemon=True).start()
        self._root.mainloop()

    def _dismiss_context_menu(self) -> None:
        try:
            self._ctx.unpost()
            self._ctx.grab_release()
        except tk.TclError:
            pass
        try:
            self._root.update_idletasks()
        except tk.TclError:
            pass

    def _run_menu_action(self, action) -> None:
        # Unpost first; defer the action so the menu can fully leave the screen.
        self._dismiss_context_menu()
        self._root.after(0, action)

    def _show_context_menu(self, event: tk.Event) -> None:
        try:
            self._ctx.tk_popup(event.x_root, event.y_root)
        finally:
            self._dismiss_context_menu()

    def _open_dashboard(self) -> None:
        webbrowser.open(DASHBOARD_URL)

    def _quit_from_window(self) -> None:
        self._stop.set()
        self._icon.stop()
        self._float.destroy()
        self._root.quit()

    def _schedule_loop(self) -> None:
        while not self._stop.is_set():
            delay = (next_auto_slot(datetime.now()) - datetime.now()).total_seconds()
            if self._stop.wait(max(1.0, delay)):
                return
            if in_auto_window(datetime.now()):
                self._refresh_async()

    def _on_refresh(self, _icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        self._refresh_async()

    def _on_open_dashboard(self, _icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        self._open_dashboard()

    def _on_toggle_click_through(
        self, _icon: pystray.Icon, _item: pystray.MenuItem
    ) -> None:
        try:
            self._root.after(0, self._toggle_click_through)
        except tk.TclError:
            pass

    def _toggle_click_through(self) -> None:
        self._click_through = not self._click_through
        self._float.set_click_through(self._click_through)
        try:
            self._icon.update_menu()
        except Exception:  # noqa: BLE001 — pystray may not support on all backends
            pass

    def _on_quit(self, _icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        self._stop.set()
        self._icon.stop()
        try:
            self._root.after(0, self._quit_ui)
        except tk.TclError:
            pass

    def _quit_ui(self) -> None:
        self._float.destroy()
        self._root.quit()

    def _refresh_async(self) -> None:
        if self._busy:
            return
        with self._refresh_lock:
            if self._busy:
                return
            self._busy = True
        threading.Thread(target=self._do_refresh, daemon=True).start()

    def _do_refresh(self) -> None:
        try:
            self._set_status("Cursor 用量 — 刷新中…", build_tray_icon("--", dim=True), pct=None, dim=True)
            token = get_access_token()
            usage = fetch_current_usage(token)
            title = format_tray_title(usage)
            tooltip = format_tooltip(usage)
            digits = icon_label(usage.primary_used_pct)
            self._set_status(
                f"{title}\n{tooltip}",
                build_tray_icon(digits, pct=usage.primary_used_pct),
                pct=usage.primary_used_pct,
                digits=digits,
            )
        except Exception as exc:  # noqa: BLE001 — show user-facing tray error
            msg = str(exc) or exc.__class__.__name__
            self._set_status(
                f"Cursor 用量 — 失败\n{msg}",
                build_tray_icon("--", pct=100),
                pct=100,
                digits="--",
                dim=False,
            )
        finally:
            self._busy = False

    def _set_status(
        self,
        tooltip: str,
        image: Image.Image,
        *,
        pct: float | None = None,
        digits: str = "--",
        dim: bool = False,
    ) -> None:
        clamped = self._clamp_tray_tooltip(tooltip)
        self._icon.icon = image
        self._icon.title = clamped
        tip_one_line = clamped.replace("\n", " · ")
        try:
            self._root.after(
                0,
                lambda: self._float.set_status(
                    digits, pct=pct, dim=dim or pct is None, tooltip=tip_one_line
                ),
            )
        except tk.TclError:
            pass

    @staticmethod
    def _clamp_tray_tooltip(text: str, max_len: int = WIN_TRAY_TIP_MAX) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if len(text) <= max_len:
            return text
        if max_len <= 1:
            return text[:max_len]
        if "\n" in text:
            first, rest = text.split("\n", 1)
            if len(first) >= max_len:
                return first[: max_len - 1] + "…"
            budget = max_len - len(first) - 1
            if budget >= 4:
                rest = " ".join(rest.split())
                return f"{first}\n{rest[: budget - 1]}…"
        return text[: max_len - 1] + "…"


def main() -> int:
    if sys.platform != "win32":
        print("此程序仅支持 Windows。", file=sys.stderr)
        return 1
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CursorUsageTray")
    TrayApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
