import json
import base64
import os
from pathlib import Path

try:
    import win32crypt
    HAS_DPAPI = True
except ImportError:
    HAS_DPAPI = False


def get_config_path() -> Path:
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        appdata = str(Path.home())
    config_dir = Path(appdata) / "ffxiv_validator"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def encrypt_secret(plain_text: str) -> str:
    """Encrypt using Windows DPAPI, returns base64 string."""
    if HAS_DPAPI:
        encrypted = win32crypt.CryptProtectData(
            plain_text.encode("utf-8"),
            "ffxiv_otp_secret",
            None, None, None, 0
        )
        return base64.b64encode(encrypted).decode("ascii")
    else:
        # Fallback: base64 only (less secure, for development/non-Windows)
        return base64.b64encode(plain_text.encode("utf-8")).decode("ascii")


def decrypt_secret(encrypted_b64: str) -> str:
    """Decrypt using Windows DPAPI from base64 string."""
    if HAS_DPAPI:
        encrypted = base64.b64decode(encrypted_b64)
        _, decrypted = win32crypt.CryptUnprotectData(
            encrypted, None, None, None, 0
        )
        return decrypted.decode("utf-8")
    else:
        return base64.b64decode(encrypted_b64).decode("utf-8")


def save_config(secret: str, launcher_title: str = "FINAL FANTASY XIV 繁體中文版",
                tab_count: int = 0, delay: float = 0.3) -> None:
    """Save encrypted secret and settings to config file."""
    config = {
        "encrypted_secret": encrypt_secret(secret),
        "launcher_window_title": launcher_title,
        "tab_count_to_otp": tab_count,
        "delay_before_type": delay,
    }
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def load_config() -> dict | None:
    """Load config. Returns dict with 'secret' and settings, or None."""
    config_path = get_config_path()
    if not config_path.exists():
        return None
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        secret = decrypt_secret(config["encrypted_secret"])
        return {
            "secret": secret,
            "launcher_window_title": config.get("launcher_window_title", "FINAL FANTASY XIV 繁體中文版"),
            "tab_count_to_otp": config.get("tab_count_to_otp", 0),
            "delay_before_type": config.get("delay_before_type", 0.3),
        }
    except Exception:
        return None
