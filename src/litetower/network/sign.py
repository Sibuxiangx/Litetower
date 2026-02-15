"""Ed25519 请求签名"""

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def generate_sign(bot_secret: str) -> bytes:
    """使用 bot secret 的前 32 字节作为种子生成 Ed25519 签名密钥对。

    Args:
        bot_secret: QQ 开放平台提供的 bot secret

    Returns:
        Ed25519 签名所需的公钥字节
    """
    seed = bot_secret.encode("utf-8")[:32]
    private_key = Ed25519PrivateKey.from_private_bytes(seed)
    public_key = private_key.public_key()
    return public_key.public_bytes_raw()
