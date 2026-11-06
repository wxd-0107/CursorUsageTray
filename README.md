# CursorUsageTray

[English](README.md) | [简体中文](README.zh-CN.md)

A lightweight **Windows-only** Cursor usage monitor written in pure Python. It shows your plan usage as an **always-on-top floating badge** plus a **system tray icon**, by reading the local Cursor login session and calling Cursor’s internal `GetCurrentPeriodUsage` API.

> Not an official Cursor product. Uses undocumented client APIs that may break after Cursor updates.

## Features

- **Floating badge** — Frameless, always on top, default near the top-right. Text format: `Cursor Usage : xx.x%`. Drag with left mouse; right-click opens a menu (Refresh / Dashboard / Quit).
- **Click-through mode** — Toggle from the **tray icon** context menu. When enabled, mouse clicks pass through the badge to windows underneath; the badge becomes slightly more transparent as a hint. Turn it off to drag or right-click the badge again.
- **Tray icon** — Black background with semibold digits (Segoe UI Semibold). One decimal place below 100 (e.g. `12.3`); full usage shows `100`. Color shifts green → yellow → red by usage.
- **Hover tooltip** — Tray tip shows used % plus Auto / API detail lines when available.
- **Auto refresh** — Weekdays **08:00–22:00**, every **30 minutes** (`:00` / `:30`). No automatic requests on weekends or overnight. Starting inside that window triggers an immediate refresh.
- **Manual refresh** — Tray or float menu **Refresh usage** anytime (not limited by the schedule).
- **Open Dashboard** — Opens the Cursor web usage page.
- **Local auth only** — Token from `%APPDATA%\Cursor\auth.json` (CLI) or `%APPDATA%\Cursor\User\globalStorage\state.vscdb` (desktop Cursor). Newer Cursor builds may encrypt tokens as `cursor-safe-storage:v1:`; this tool decrypts on Windows via DPAPI + AES-GCM locally (keys never leave the machine).

## Requirements

- Windows 10/11
- Python **3.10+** (tested with 3.13)
- Cursor desktop signed in, or `agent login` completed

## Quick start

1. Sign in to **Cursor desktop** (or run `agent login`).
2. Double-click **`run.vbs`** (no console window), **or** in the project folder:

```bat
python -m pip install -r requirements.txt
pythonw main.py
```

- Prefer **`run.vbs`** for daily use (silent dependency install + `pythonw`).
- **`run.bat`** also launches with `pythonw`, but double-clicking from Explorer may flash a console briefly. Pass any argument to `run.bat` to run the bat path directly (e.g. `run.bat go`).

After start, a floating badge appears near the top-right; the tray icon is in the notification area (drag it out from the overflow `^` if hidden).

## Optional: start with Windows

1. `Win + R` → `shell:startup` → Enter.
2. Create a shortcut to **`run.vbs`** in that folder.

## Usage tips

| Action | Where |
|--------|--------|
| Drag badge | Left-drag on the float |
| Float menu | Right-click the float |
| Refresh / Dashboard / Quit | Float menu or tray menu |
| Click-through on/off | **Tray** menu → **穿透模式** (Click-through) |

## Notes & privacy

- Uses Cursor’s internal dashboard API, **not** a public official API.
- `accessToken` is read only on this PC and is not uploaded to any third-party server.
- If login looks expired, reopen Cursor or run `agent login`, then refresh.

## Project layout

| File | Role |
|------|------|
| `main.py` | App entry: float + tray UI, scheduling, refresh |
| `float_window.py` | Always-on-top draggable badge & click-through |
| `tray_icon.py` | Numeric tray / badge icon rendering |
| `cursor_api.py` | Fetch usage & format display strings |
| `cursor_auth.py` | Locate and load access token |
| `cursor_safe_storage.py` | Decrypt Cursor safeStorage on Windows |
| `requirements.txt` | Python dependencies |
| `run.vbs` | Silent install + start (recommended) |
| `run.bat` | Install + start (console-friendly / debug) |

## License

Use and modify for personal purposes. No warranty.
