import time
import base64
from urllib.parse import urlparse, parse_qs
import pyotp


def extract_secret(input_str: str) -> str:
    """Extract base32 secret from raw key or otpauth:// URI."""
    input_str = input_str.strip()
    if input_str.lower().startswith("otpauth://"):
        parsed = urlparse(input_str)
        params = parse_qs(parsed.query)
        secret = params.get("secret", [None])[0]
        if not secret:
            raise ValueError("otpauth URI missing secret parameter")
        return secret.replace(" ", "").upper()
    return input_str.replace(" ", "").upper()


def validate_secret(input_str: str) -> bool:
    """Check if the input is a valid base32 secret or otpauth:// URI."""
    try:
        secret = extract_secret(input_str)
        padding = (8 - len(secret) % 8) % 8
        base64.b32decode(secret + "=" * padding)
        return True
    except Exception:
        return False


def generate_otp(input_str: str) -> str:
    """Generate current 6-digit TOTP code."""
    secret = extract_secret(input_str)
    totp = pyotp.TOTP(secret)
    return totp.now()


def get_time_remaining() -> int:
    """Seconds remaining before the current TOTP code rotates."""
    return 30 - int(time.time() % 30)
