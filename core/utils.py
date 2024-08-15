import os
import sys
import jwt
import time
import json
import httpx
import base64
import random
import jwt.algorithms
import pyzstd
import hashlib
import aiofiles
from pathlib import Path
from loguru import logger
from string import Template
from random import choice, choices

import core.const as const
import core.settings as settings
import core.datafile as datafile
from core.types import Cluster, FileObject, Avro
from core.upstream import Upstream

def fi(template_str, variables):  
    """  
    使用变量字典替换模板字符串中的变量。
    - 【参数】模板字符串：`包含要替换的变量的模板字符串`。

    - 【参数】替换的变量字典：`要在模板字符串中替换的变量字典`。

    - 返回结果：`替换了变量的模板字符串`。
    """  
    template = Template(template_str)  
    replaced_str = template.substitute(variables)  
    return replaced_str

USERAGENT = fi(str(settings.settings.get('USERAGENT', 'iodine-ctrl')), {"version": settings.VERSION})

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
    return random.choice(const.all_figures + const.all_small_letters)

# 随机生成字符串
def generate_random_token(length):
    result = ''
    for i in range(length):
        result += generate_random_character()
    return result

# 文件 SHA-1 值
def hash_file(filename: Path, algorithm: str | None = 'sha1'):
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

        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        
        unix_style_dirpath = dirpath.replace('\\', '/')
        for filename in filenames:
            if filename.startswith('.'):
                continue
            filepath = f"{unix_style_dirpath}/{filename}"
            files_list.append(FileObject(filepath))

    return files_list

# 保存经计算、压缩过的 Avro 格式 和 JSON 格式的文件列表
def save_calculate_filelist():
    files_list = scan_files('./files/')
    filelist_json = {}
    # 挨个写入数据
    for file in files_list:
        filelist_json[file.hash] = {
            "path": f"{file.path}", # 文件路径
        }
    datafile.write_json_to_file_noasync("filelist.json", filelist_json)
    avro = Avro()
    avro.writeVarInt(len(files_list)) # 写入文件数量
    for file in files_list:
        avro.writeString(file.path)
        avro.writeString(file.hash)
        avro.writeVarInt(file.size)
        avro.writeVarInt(file.mtime)
    avro.write(b'\x00')
    result = pyzstd.compress(avro.io.getvalue())
    avro.io.close()
    datafile.write_filelist_to_cache_nosaync("filelist.avro", result)
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
    
    timestamp = int((time.time() + 5 * 60) * 1000)
    e = base36encode(timestamp)
    sign_data = (secret + path + e).encode('utf-8')
    sha1.update(sign_data)
    sign_bytes = sha1.digest()
    sign = to_url_safe_base64_string(sign_bytes).replace("=", "")
    return f"?s={sign}&e={e}"

# 获取节点mesure的url
def get_url(host: str, port: str, path: str, sign: str):
    url = f"http://{host}:{port}{path}{sign}"
    return url

# 对节点进行测速
async def measure_cluster(size: int, cluster):
    path = f"/measure/{str(size)}"
    sign = get_sign(path, cluster["secret"])
    url = get_url(cluster["host"], cluster["port"], path, sign)
    try:
        start_time = time.time()
        user_agent = choice(const.user_agent_list)
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers={"User-Agent": user_agent})
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        # 计算测速时间
        bandwidth = size / elapsed_time * 8 # 计算带宽
        return [True, bandwidth]
    except Exception as e:
        return [False, e]
    
# 算哈希
def compute_hash(file_stream):
    """计算文件流的 SHA-256 哈希值"""
    hasher = hashlib.sha256()
    for chunk in iter(lambda: file_stream.read(4096), b""):
        hasher.update(chunk)
    return hasher.hexdigest()

# 节点enable时进行文件校验
async def check_cluster(url, file_path):
    """检查URL返回的内容与文件内容的哈希值是否匹配"""
    is_valid = False
    
    # 发送请求并获取响应
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers={"User-Agent": choice(const.user_agent_list)})
    
    # 计算响应内容的哈希值
    response_hash = compute_hash(response.raw)
    
    # 读取文件并计算文件的哈希值
    with aiofiles.open(file_path, 'rb') as file:
        file_hash = compute_hash(file)
    
    # 比较哈希值
    if response_hash == file_hash:
        is_valid = True
    
    response.close()
    return is_valid

# 随机挑选幸运儿(文件)
def choose_file(files : list[FileObject], num: int) -> list[FileObject]:
    return random.sample(files, num)

# print(choose_file(5))
# 计算请求数据量
def hum_convert(value: int):
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    size = value
    for unit in units:
        if (size / 1024) < 1:
            return "%.2f%s" % (size, unit)
        size = size / 1024
    return f"{value:.2f}"

def extract_repo_name(url: str) -> str:
    # 移除 URL 结尾的 .git
    repo_name_with_git = url.split('/')[-1]
    repo_name = repo_name_with_git.rsplit('.', 1)[0]

    return repo_name