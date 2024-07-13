import sys
import jwt
import random
from pathlib import Path
from loguru import logger
import core.settings as settings

logging = logger
logging.remove()
logging.add(sys.stdout, format="<green>{level}</green>:     {message}", level="INFO")
logging.add(sys.stdout, format="<red>{level}</red>:     {message}", level="ERROR")
logging.add(sys.stdout, format="<yellow>{level}</yellow>:     {message}", level="WARNING")

all_figures = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
all_small_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
def generate_jwt_token(data, secret: str | None = settings.JWT_SECRET):
    result = jwt.encode(data, secret, algorithm='HS256')
    return result

def generate_random_character():
    return random.choice(all_figures + all_small_letters)

def generate_random_token(length):
    result = ''
    for i in range(length):
        result += generate_random_character()
    return result