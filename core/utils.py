import os
import sys
import jwt
import time
import json
import httpx
import base64
import random
import pyzstd
import hashlib
import aiofiles
from pathlib import Path
from loguru import logger

import core.settings as settings
from core.types import Cluster, FileObject, Avro

logging = logger
logging.remove()
logging.add(sys.stdout, format="<green>{level}</green>:     {message}", level="INFO")
logging.add(sys.stdout, format="<red>{level}</red>:     {message}", level="ERROR")
logging.add(sys.stdout, format="<yellow>{level}</yellow>:     {message}", level="WARNING")

all_figures = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
all_small_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

# 读缓存
def read_from_cache(filename: str):
    cache_file = Path(f"./data/{filename}")
    with open(cache_file, "rb") as f:
        filelist_content = f.read()
        filelist = filelist_content
    return filelist

# 写缓存
def write_to_cache(filename: str, filelist):
    cache_file = Path(f"./data/{filename}")
    with open(cache_file, 'wb') as f:
        f.write(filelist)

# JWT 加密
def encode_jwt(data, secret: str | None = settings.JWT_SECRET):
    result = jwt.encode(data, secret, algorithm='HS256')
    return result

# JWT 解密
def decode_jwt(data, secret: str | None = settings.JWT_SECRET):
    result = jwt.decode(data, secret, algorithms=['HS256'])
    return result

# 随机生成字符
def generate_random_character():
    return random.choice(all_figures + all_small_letters)

# 随机生成字符串
def generate_random_token(length):
    result = ''
    for i in range(length):
        result += generate_random_character()
    return result

# 文件 SHA-1 值
def hash_file(filename, algorithm: str | None = 'sha1'):
    """此函数返回传入文件的 SHA-1 或其他哈希值（取决于指定的算法）"""
    # 根据算法创建哈希实例
    hash_algorithm = hashlib.new(algorithm)
    
    # 以二进制模式打开文件
    with open(filename, "rb") as file:
        # 逐块读取并更新哈希值，每块大小为4KB
        for byte_block in iter(lambda: file.read(4096), b""):
            hash_algorithm.update(byte_block)
            
    # 返回哈希值的十六进制形式
    return hash_algorithm.hexdigest()

# 扫文件
def scan_files(directory_path: Path):
    """* 递归扫描目录及其子目录，返回该目录下所有文件的路径集合"""
    files_list = []
    files_list.clear()

    for dirpath, dirnames, filenames in os.walk(directory_path):

        unix_style_dirpath = dirpath.replace('\\', '/')
        
        for filename in filenames:
            if filename.startswith('.'):
                continue
            filepath = f"{unix_style_dirpath}/{filename}"
            files_list.append(FileObject(filepath))

    return files_list

# 保存经计算、压缩过的 Avro 格式的文件列表
def save_calculate_filelist():
    files_list = scan_files('./files/')
    avro = Avro()
    avro.writeVarInt(len(files_list))
    # 挨个写入数据
    for file in files_list:
        avro.writeString(file.path)
        avro.writeString(file.hash)
        avro.writeVarInt(file.size)
        avro.writeVarInt(file.mtime)
    avro.write(b'\x00')
    result = pyzstd.compress(avro.io.getvalue())
    write_to_cache("filelist.avro", result)
    logger.info("文件列表计算成功，已保存至本地。")
    return result

def to_url_safe_base64_string(byte_data):
    return base64.urlsafe_b64encode(byte_data).rstrip(b'=').decode('utf-8')

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

# 获取节点 sign
def get_sign(path, secret):
    try:
        sha1 = hashlib.sha1()
    except Exception as e:
        logger.error(e)
        return None
    
    timestamp = int(time.time() * 1000 + 5 * 60)
    e = base36encode(timestamp)
    sign_data = (secret + path + e).encode('utf-8')
    sha1.update(sign_data)
    sign_bytes = sha1.digest()
    sign = to_url_safe_base64_string(sign_bytes).replace("=", "")
    return f"?s={sign}&e={e}"

def get_url(host: str, port: str, path: str, sign: str):
    url = f"http://{host}:{port}{path}{sign}"
    return url
    
async def measure_cluster(size: int, cluster):
    path = f"/measure/{str(size)}"
    sign = get_sign(path, cluster["secret"])
    url = get_url(cluster["host"], cluster["port"], path, sign)
    logger.info(url)
    try:
        start_time = time.time()
        async with httpx.AsyncClient() as client:
            await client.get(url)
        end_time = time.time()
        elapsed_time = end_time - start_time
        # 计算测速时间
        bandwidth = size / elapsed_time * 8 # 计算带宽
        return [True, bandwidth]
    except Exception as e:
        return [False, e]
    
def hum_convert(value: int):
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    size = 1024.0
    for i in range(len(units)):
        if (value / size) < 1:
            return "%.2f%s" % (value, units[i])
        value = value / size