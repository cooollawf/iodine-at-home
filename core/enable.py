"""
    这里是节点enable所需的一些函数
"""

import hashlib
import base64
import time

class Cluster:
    def __init__(self, secret):
        self.secret = secret

def to_url_safe_base64_string(byte_data):
    return base64.urlsafe_b64encode(byte_data).rstrip(b'=').decode('utf-8')

def get_sign(path, cluster):
    try:
        sha1 = hashlib.sha1()
    except Exception as e:
        print(e)
        return None

    timestamp = int(time.time() + 5 * 60)
    e = base36encode(timestamp)
    sign_data = (cluster.secret + path + e).encode('utf-8')
    sha1.update(sign_data)
    sign_bytes = sha1.digest()
    sign = to_url_safe_base64_string(sign_bytes)
    # print(f"?s={sign}&e={e}")
    return f"?s={sign}&e={e}"

# 将整数转换为base36字符串
def base36encode(number):
    if not isinstance(number, int):
        raise TypeError('number must be an integer')
    if number < 0:
        raise ValueError('number must be positive')

    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
    base36 = ''
    while number:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36
    return base36 or alphabet[0]