import base64
import hashlib
import hmac
import json
import time
import secrets

from backend.app.config import JWT_SECRET_KEY


PAYMENT_SESSION_TTL = 15 * 60  # 15 minutes


def _encode(data: dict) -> str:
    raw = json.dumps(
        data,
        separators=(",", ":"),
    ).encode()

    return base64.urlsafe_b64encode(
        raw
    ).decode().rstrip("=")


def _decode(value: str) -> dict:
    padding = "=" * (-len(value) % 4)

    raw = base64.urlsafe_b64decode(
        value + padding
    )

    return json.loads(raw.decode())


def create_payment_session(
    payment_id: int,
    user_id: int,
) -> str:

    payload = {
        "payment_id": payment_id,
        "user_id": user_id,
        "exp": int(time.time()) + PAYMENT_SESSION_TTL,
        "nonce": secrets.token_hex(16),
    }

    encoded = _encode(payload)

    signature = hmac.new(
        JWT_SECRET_KEY.encode(),
        encoded.encode(),
        hashlib.sha256,
    ).hexdigest()

    return f"{encoded}.{signature}"


def verify_payment_session(
    token: str,
    payment_id: int,
) -> int:

    try:
        encoded, provided_signature = token.split(
            ".",
            1,
        )

        expected_signature = hmac.new(
            JWT_SECRET_KEY.encode(),
            encoded.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(
            provided_signature,
            expected_signature,
        ):
            raise ValueError(
                "Invalid payment session"
            )

        payload = _decode(encoded)

        if int(payload["payment_id"]) != int(payment_id):
            raise ValueError(
                "Payment session does not match payment"
            )

        if int(payload["exp"]) < int(time.time()):
            raise ValueError(
                "Payment session has expired"
            )

        return int(payload["user_id"])

    except Exception as exc:
        raise ValueError(
            "Invalid or expired payment session"
        ) from exc