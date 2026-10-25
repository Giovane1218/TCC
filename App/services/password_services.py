import hashlib
import hmac
import secrets


PASSWORD_ITERATIONS = 600_000

def hash_password(password: str) -> str:
    # O salt aleatório torna cada hash único; PBKDF2 dificulta tentativas rápidas de senha.
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS, salt.hex(), password_hash.hex()
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, expected_hex = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        expected_hash = bytes.fromhex(expected_hex)
    except (TypeError, ValueError):
        return False

    return hmac.compare_digest(actual_hash, expected_hash)