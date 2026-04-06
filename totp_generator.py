import time
import base64
import pyotp


def validate_secret(secret: str) -> bool:
    """Check if the secret is valid base32."""
    try:
        cleaned = secret.replace(" ", "").upper()
        # Add padding if needed — many TOTP secrets omit trailing '='
        padding = (8 - len(cleaned) % 8) % 8
        base64.b32decode(cleaned + "=" * padding)
        return True
    except Exception:
        return False


def generate_otp(secret: str) -> str:
    """Generate current 6-digit TOTP code."""
    cleaned = secret.replace(" ", "").upper()
    totp = pyotp.TOTP(cleaned)
    return totp.now()


def get_time_remaining() -> int:
    """Seconds remaining before the current TOTP code rotates."""
    return 30 - int(time.time() % 30)
