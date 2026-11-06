"""Always-on-top floating usage badge (frameless, draggable)."""

from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from typing import Callable

from tray_icon import icon_label, usage_color

# Wide enough for "Cursor Usage : 100%"
WIN_W = 188
WIN_H = 36
PAD_X = 12
PAD_Y = 6
BG = "#121212"
FG_DIM = "#b0b0b0"
BORDER = "#2a2a2a"
LABEL_PREFIX = "Cursor Usage : "
ALPHA_NORMAL = 0.94
ALPHA_CLICK_THROUGH = 0.55

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020


class FloatWindow:
    """Small topmost badge showing Cursor usage percent."""

    def __init__(
        self,
        root: tk.Tk,
        *,
        on_right_click: Callable[[tk.Event], None] | None = None,
        on_close: Callable[[], None] | None = None,
    ) -> None:
        self._root = root
        self._on_right_click = on_right_click
        self._on_close = on_close
        self._drag_ox = 0
        self._drag_oy = 0
        self._click_through = False

        self._win = tk.Toplevel(root)
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        try:
            self._win.attributes("-alpha", ALPHA_NORMAL)
        except tk.TclError:
            pass
        self._win.configure(bg=BG)
        self._win.resizable(False, False)
        self._win.protocol("WM_DELETE_WINDOW", self._handle_close)

        self._frame = tk.Frame(
            self._win,
            bg=BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=PAD_X,
            pady=PAD_Y,
        )
        self._frame.pack(fill=tk.BOTH, expand=True)

        self._text = tk.Label(
            self._frame,
            text=f"{LABEL_PREFIX}--%",
            fg=FG_DIM,
            bg=BG,
            font=("Segoe UI Semibold", 11),
            bd=0,
            highlightthickness=0,
        )
        self._text.pack()

        for widget in (self._win, self._frame, self._text):
            widget.bind("<ButtonPress-1>", self._on_press)
            widget.bind("<B1-Motion>", self._on_motion)
            widget.bind("<Button-3>", self._handle_right_click)

        self._place_default()
        self.set_status("--", dim=True, tooltip="Cursor 用量 — 加载中")

    @property
    def window(self) -> tk.Toplevel:
        return self._win

    @property
    def click_through(self) -> bool:
        return self._click_through

    def set_click_through(self, enabled: bool) -> None:
        """When enabled, mouse events pass through to windows underneath."""
        self._click_through = bool(enabled)
        if not self._win.winfo_exists():
            return
        self._win.update_idletasks()
        try:
            self._win.attributes(
                "-alpha",
                ALPHA_CLICK_THROUGH if self._click_through else ALPHA_NORMAL,
            )
            self._win.attributes("-topmost", True)
        except tk.TclError:
            pass
        if sys.platform == "win32":
            self._apply_win_click_through(self._click_through)

    def _apply_win_click_through(self, enabled: bool) -> None:
        user32 = ctypes.windll.user32
        # Apply to both the Tk widget HWND and its parent frame if present.
        hwnds: list[int] = []
        hwnd = int(self._win.winfo_id())
        while hwnd and hwnd not in hwnds:
            hwnds.append(hwnd)
            hwnd = int(user32.GetParent(hwnd) or 0)
        for hwnd in hwnds:
            style = int(user32.GetWindowLongW(hwnd, GWL_EXSTYLE))
            style |= WS_EX_LAYERED
            if enabled:
                style |= WS_EX_TRANSPARENT
            else:
                style &= ~WS_EX_TRANSPARENT
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    def _place_default(self) -> None:
        self._root.update_idletasks()
        sw = self._root.winfo_screenwidth()
        x = max(8, sw - WIN_W - 24)
        y = 48
        self._win.geometry(f"{WIN_W}x{WIN_H}+{x}+{y}")

    def _on_press(self, event: tk.Event) -> None:
        self._drag_ox = event.x_root - self._win.winfo_x()
        self._drag_oy = event.y_root - self._win.winfo_y()

    def _on_motion(self, event: tk.Event) -> None:
        x = event.x_root - self._drag_ox
        y = event.y_root - self._drag_oy
        self._win.geometry(f"+{x}+{y}")

    def _handle_right_click(self, event: tk.Event) -> None:
        if self._on_right_click:
            self._on_right_click(event)

    def _handle_close(self) -> None:
        if self._on_close:
            self._on_close()

    def set_status(
        self,
        digits: str,
        *,
        pct: float | None = None,
        dim: bool = False,
        tooltip: str = "",
    ) -> None:
        if not self._win.winfo_exists():
            return

        value = digits if digits.endswith("%") else f"{digits}%"
        label = f"{LABEL_PREFIX}{value}"
        if dim or pct is None:
            color = FG_DIM
        else:
            r, g, b, _a = usage_color(pct)
            color = f"#{r:02x}{g:02x}{b:02x}"
        self._text.configure(text=label, fg=color)

        tip = (tooltip or "").replace("\n", " · ").strip()
        if tip:
            self._win.title(tip[:120])

    def set_from_pct(
        self,
        pct: float | None,
        *,
        dim: bool = False,
        tooltip: str = "",
    ) -> None:
        digits = icon_label(pct)
        self.set_status(digits, pct=pct, dim=dim or pct is None, tooltip=tooltip)

    def destroy(self) -> None:
        try:
            self._win.destroy()
        except tk.TclError:
            pass
