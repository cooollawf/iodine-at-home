# 第三方库
import jwt

# 自定义库
from core.config import config


# JWT 加密
def encode_jwt(data, secret: str | None = config.get("jwt-secret")):
    result = jwt.encode(data, secret, algorithm="HS256")
    return result


# JWT 解密
def decode_jwt(data, secret: str | None = config.get("jwt-secret")):
    result = jwt.decode(data, secret, algorithms=["HS256"])
    return result
