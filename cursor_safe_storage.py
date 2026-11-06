"""Decrypt Cursor Electron safeStorage values on Windows."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

SAFE_PREFIX = "cursor-safe-storage:v1:"


def _local_state_path() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA 未设置")
    return Path(appdata) / "Cursor" / "Local State"


def _load_master_key() -> bytes:
    path = _local_state_path()
    if not path.is_file():
        raise RuntimeError(f"未找到 Cursor Local State: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        encrypted_key_b64 = data["os_crypt"]["encrypted_key"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise RuntimeError("无法读取 Cursor os_crypt 密钥") from exc

    encrypted_key = base64.b64decode(encrypted_key_b64)
    if encrypted_key.startswith(b"DPAPI"):
        encrypted_key = encrypted_key[5:]

    try:
        import win32crypt  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError("需要 pywin32：pip install pywin32") from exc

    try:
        _desc, master_key = win32crypt.CryptUnprotectData(
            encrypted_key, None, None, None, 0
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("DPAPI 解密失败（请用当前 Windows 用户运行）") from exc

    return master_key


def _decrypt_v10_blob(blob: bytes, master_key: bytes) -> str:
    if len(blob) < 3 + 12 + 16:
        raise ValueError("密文过短")
    prefix = blob[:3]
    if prefix not in (b"v10", b"v11"):
        try:
            import win32crypt  # type: ignore[import-untyped]

            _desc, plain = win32crypt.CryptUnprotectData(blob, None, None, None, 0)
            return plain.decode("utf-16-le", errors="replace").rstrip("\x00")
        except Exception as exc:  # noqa: BLE001
            raise ValueError("未知密文格式") from exc

    try:
        from Crypto.Cipher import AES  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError("需要 pycryptodome：pip install pycryptodome") from exc

    nonce = blob[3:15]
    sealed = blob[15:]
    cipher = AES.new(master_key, AES.MODE_GCM, nonce=nonce)
    plain = cipher.decrypt_and_verify(sealed[:-16], sealed[-16:])
    return plain.decode("utf-8")


def decrypt_stored_value(raw: str) -> str:
    text = raw.strip()
    if not text.startswith(SAFE_PREFIX):
        return text
    payload_b64 = text[len(SAFE_PREFIX) :].strip()
    blob = base64.b64decode(payload_b64)
    master_key = _load_master_key()
    return _decrypt_v10_blob(blob, master_key)
