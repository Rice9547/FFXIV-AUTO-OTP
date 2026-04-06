import base64
import struct
from urllib.parse import urlparse, parse_qs, unquote

from PIL import Image, ImageGrab
from pyzbar.pyzbar import decode as decode_qr


def read_qr_from_image(image_path: str) -> str | None:
    """Read QR code content from an image file. Returns decoded string or None."""
    img = Image.open(image_path)
    results = decode_qr(img)
    if results:
        return results[0].data.decode("utf-8")
    return None


def read_qr_from_clipboard() -> str | None:
    """Read QR code content from clipboard image. Returns decoded string or None."""
    img = ImageGrab.grabclipboard()
    if img is None:
        return None
    results = decode_qr(img)
    if results:
        return results[0].data.decode("utf-8")
    return None


def _read_varint(data: bytes, pos: int) -> tuple[int, int]:
    """Read a protobuf varint, return (value, new_pos)."""
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        result |= (b & 0x7F) << shift
        pos += 1
        if (b & 0x80) == 0:
            break
        shift += 7
    return result, pos


def _parse_otp_parameters(data: bytes) -> dict | None:
    """Parse a single OtpParameters protobuf message."""
    pos = 0
    secret = None
    name = ""
    issuer = ""
    while pos < len(data):
        tag_wire, pos = _read_varint(data, pos)
        field_number = tag_wire >> 3
        wire_type = tag_wire & 0x07

        if wire_type == 0:  # varint
            _, pos = _read_varint(data, pos)
        elif wire_type == 2:  # length-delimited
            length, pos = _read_varint(data, pos)
            field_data = data[pos:pos + length]
            pos += length
            if field_number == 1:  # secret (bytes)
                secret = base64.b32encode(field_data).decode("ascii").rstrip("=")
            elif field_number == 2:  # name
                name = field_data.decode("utf-8")
            elif field_number == 3:  # issuer
                issuer = field_data.decode("utf-8")
        else:
            break

    if secret:
        return {"secret": secret, "name": name, "issuer": issuer}
    return None


def parse_otpauth_migration(uri: str) -> list[dict]:
    """Parse otpauth-migration://offline?data=... URI from Google Authenticator export."""
    parsed = urlparse(uri)
    params = parse_qs(parsed.query)
    data_b64 = params.get("data", [None])[0]
    if not data_b64:
        return []

    data = base64.b64decode(data_b64)
    results = []
    pos = 0

    while pos < len(data):
        tag_wire, pos = _read_varint(data, pos)
        field_number = tag_wire >> 3
        wire_type = tag_wire & 0x07

        if wire_type == 2:  # length-delimited
            length, pos = _read_varint(data, pos)
            field_data = data[pos:pos + length]
            pos += length
            if field_number == 1:  # otp_parameters
                entry = _parse_otp_parameters(field_data)
                if entry:
                    results.append(entry)
        elif wire_type == 0:  # varint
            _, pos = _read_varint(data, pos)
        else:
            break

    return results


def _parse_qr_content(content: str) -> list[dict]:
    """Parse QR code content string into TOTP entries."""
    if content.startswith("otpauth-migration://"):
        return parse_otpauth_migration(content)
    elif content.startswith("otpauth://"):
        parsed = urlparse(content)
        params = parse_qs(parsed.query)
        secret = params.get("secret", [None])[0]
        if secret:
            name = unquote(parsed.path.lstrip("/"))
            issuer = params.get("issuer", [""])[0]
            return [{"secret": secret, "name": name, "issuer": issuer}]
    return []


def parse_qr_image(image_path: str) -> list[dict]:
    """Parse a QR code image file and extract TOTP secrets."""
    content = read_qr_from_image(image_path)
    if not content:
        return []
    return _parse_qr_content(content)


def parse_qr_clipboard() -> list[dict]:
    """Parse a QR code from clipboard image and extract TOTP secrets."""
    content = read_qr_from_clipboard()
    if not content:
        return []
    return _parse_qr_content(content)
