"""Read Cursor session token from local auth storage (Windows)."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from cursor_safe_storage import decrypt_stored_value

TOKEN_KEY = "cursorAuth/accessToken"


def _appdata() -> Path:
    root = os.environ.get("APPDATA")
    if not root:
        raise RuntimeError("APPDATA 未设置，无法定位 Cursor 配置目录")
    return Path(root)


def auth_json_path() -> Path:
    return _appdata() / "Cursor" / "auth.json"


def state_db_path() -> Path:
    return _appdata() / "Cursor" / "User" / "globalStorage" / "state.vscdb"


def _normalize_token(raw: str) -> str | None:
    value = raw.strip()
    if not value:
        return None
    if value.startswith('"') and value.endswith('"'):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    if value.startswith("cursor-safe-storage:"):
        try:
            value = decrypt_stored_value(value)
        except RuntimeError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"解密 Cursor 登录信息失败: {exc}") from exc
    return value.strip()


def read_token_from_auth_json(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    token = data.get("accessToken")
    if isinstance(token, str):
        return _normalize_token(token)
    return None


def read_token_from_db(path: Path) -> str | None:
    if not path.is_file():
        return None
    uri = f"file:{path.as_posix()}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=2.0)
    except sqlite3.Error:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT value FROM ItemTable WHERE key = ?", (TOKEN_KEY,))
        row = cur.fetchone()
        if not row or row[0] is None:
            return None
        raw = row[0]
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        return _normalize_token(str(raw))
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def get_access_token() -> str:
    """CLI auth.json first, then desktop Cursor state.vscdb."""
    token = read_token_from_auth_json(auth_json_path())
    if token:
        return token

    token = read_token_from_db(state_db_path())
    if token:
        return token

    raise RuntimeError(
        "未找到 Cursor 登录信息。请先打开 Cursor 并登录，或运行 agent login。"
    )
