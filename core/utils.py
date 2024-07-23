import os
import io
import sys
import jwt
import httpx
import random
import hashlib
import fastavro
import aiofiles
import pyzstd as zstd
from pathlib import Path
from loguru import logger

import core.settings as settings
from core.types import Cluster, FileObject

logging = logger
logging.remove()
logging.add(sys.stdout, format="<green>{level}</green>:     {message}", level="INFO")
logging.add(sys.stdout, format="<red>{level}</red>:     {message}", level="ERROR")
logging.add(sys.stdout, format="<yellow>{level}</yellow>:     {message}", level="WARNING")

files_list = []

AVRO_SCHEMA = {
    'type': 'array',
    'items': {
        'name': 'FileListEntry',
        'type': 'record',
        'fields': [
            {'name': 'path', 'type': 'string'},
            {'name': 'hash', 'type': 'string'},
            {'name': 'size', 'type': 'long'},
            {'name': 'mtime', 'type': 'long'}
        ]
    }
}

all_figures = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
all_small_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
def encode_jwt(data, secret: str | None = settings.JWT_SECRET):
    result = jwt.encode(data, secret, algorithm='HS256')
    return result

def decode_jwt(data, secret: str | None = settings.JWT_SECRET):
    result = jwt.decode(data, secret, algorithms=['HS256'])
    return result

def generate_random_character():
    return random.choice(all_figures + all_small_letters)

def generate_random_token(length):
    result = ''
    for i in range(length):
        result += generate_random_character()
    return result

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

def scan_files(directory_path: Path):
    """* 递归扫描目录及其子目录，返回该目录下所有文件的路径集合"""
    files_list.clear()

    for dirpath, dirnames, filenames in os.walk(directory_path):

        unix_style_dirpath = dirpath.replace('\\', '/')
        
        for filename in filenames:
            if filename.startswith('.'):
                continue
            filepath = f"{unix_style_dirpath}/{filename}"
            files_list.append(FileObject(filepath, hash_file(filepath), os.path.getsize(filepath), os.path.getmtime(filepath)*1000))
    logger.info(files_list)
    return files_list

def compute_avro_bytes(elements):
    out = io.BytesIO()
    # out.write(len(elements).to_bytes(4, byteorder='big'))
    fastavro.writer(out, AVRO_SCHEMA, ([{'path': file.path,'hash': file.hash,'size': file.size, 'mtime': file.mtime} for file in files_list]))
    bytes_data = out.getvalue()

    result = zstd.ZstdCompressor().compress(bytes_data)

    return result

# async def get_sign(file: str, cluster: str):
    

# async def check_cluster(url):
#     is_valid = False
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url, headers=settings.HEADERS)
#     if response
