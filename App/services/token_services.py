import base64
import binascii
import hashlib
import hmac
import json
import os
import time
from typing import Any

from core.exceptions.exceptions_type import LoggedOutError

TOKEN_LIFETIME_SECONDS = 60 * 60


def _token_secret() -> bytes:
    secret = os.getenv("AUTH_SECRET_KEY")
    if not secret or len(secret) < 32:
        raise RuntimeError(
            "AUTH_SECRET_KEY precisa estar configurada com pelo menos 32 caracteres."
        )
    return secret.encode("utf-8")


def _encode_segment(value: dict[str, Any]) -> str:
    return (
        base64.urlsafe_b64encode(
            json.dumps(value, separators=(",", ":")).encode("utf-8")
        )
        .rstrip(b"=")
        .decode("ascii")
    )


def create_access_token(user_identifier: str) -> str:
    now = int(time.time())
    header = _encode_segment({"alg": "HS256", "typ": "JWT"})
    payload = _encode_segment(
        {"sub": user_identifier, "iat": now, "exp": now + TOKEN_LIFETIME_SECONDS}
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    signature = hmac.new(_token_secret(), signing_input, hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    return f"{header}.{payload}.{encoded_signature}"


def _decode_access_token(token: str) -> str:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")

        def decode_segment(segment: str) -> Any:
            padded = segment + "=" * (-len(segment) % 4)
            return json.loads(base64.urlsafe_b64decode(padded))

        header = decode_segment(header_segment)
        payload = decode_segment(payload_segment)
        if (
            not isinstance(header, dict)
            or not isinstance(payload, dict)
            or header.get("alg") != "HS256"
        ):
            raise LoggedOutError()

        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        expected_signature = hmac.new(
            _token_secret(), signing_input, hashlib.sha256
        ).digest()
        supplied_signature = base64.urlsafe_b64decode(
            signature_segment + "=" * (-len(signature_segment) % 4)
        )
        if not hmac.compare_digest(expected_signature, supplied_signature):
            raise LoggedOutError()

        user_identifier = payload["sub"]
        if not isinstance(user_identifier, str) or int(payload["exp"]) <= int(
            time.time()
        ):
            raise LoggedOutError()
        return user_identifier
    except LoggedOutError:
        raise
    except (ValueError, TypeError, KeyError, UnicodeError, binascii.Error):
        raise LoggedOutError() from None
