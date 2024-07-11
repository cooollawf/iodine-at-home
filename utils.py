import jwt
from loguru import logger

import config

def generate_jwt_token(data):
    token = jwt.encode(data, config.JWT_SECRET, algorithm='HS256')
    return token
