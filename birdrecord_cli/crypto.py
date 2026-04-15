"""AES envelope decryption."""

import base64
import json
from typing import Any, Mapping

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from birdrecord_cli.constants import AES_IV, AES_KEY


def decrypt_aes_cbc_b64(ciphertext_b64: str) -> bytes:
    raw = base64.b64decode(ciphertext_b64)
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return unpad(cipher.decrypt(raw), AES.block_size)


def parse_encrypted_envelope(envelope: Mapping[str, Any]) -> Any:
    """Decrypt ``envelope[field]`` when encrypted; else first non-null of ``data`` / ``result``."""
    if envelope.get("hasNeedEncrypt") and envelope.get("field"):
        field = envelope["field"]
        blob = envelope.get(field)
        if isinstance(blob, str):
            plain = decrypt_aes_cbc_b64(blob)
            return json.loads(plain.decode("utf-8"))
    if envelope.get("data") is not None:
        return envelope["data"]
    if envelope.get("result") is not None:
        return envelope["result"]
    return None
