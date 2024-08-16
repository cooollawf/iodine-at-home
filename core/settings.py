import os
import sys
import yaml
import httpx
from pathlib import Path
from core.logger import logger
from dotenv import load_dotenv, dotenv_values

versionPath = Path('./VERSION')
dotenvPath = Path('./settings/.env')

with open(versionPath, 'r', encoding='UTF-8') as versionFile:
    VERSION = versionFile.read()

# 尝试打开配置文件
env_status = load_dotenv(dotenvPath)

if env_status == False:
    logger.info("配置文件发生丢失，已创建一个空白文件。")
    with open(dotenvPath, 'w') as cfgFile:
        cfgFile.write('')
    logger.success(f"空白文件新建成功，你应该将 .env.example 内所有内容复制进 .env 并修改后运行程序。")
    sys.exit(0)

# 读取配置文件信息
settings = dotenv_values(dotenvPath)

HOST = str(settings.get('HOST', '0.0.0.0'))
PORT = int(settings.get('PORT', 8080))
ACCESS_LOG_CONTENT = settings.get('ACCESS_LOG', 'true').lower()
JWT_SECRET = str(settings.get('JWT_SECRET', '114514'))
TOKEN = str(settings.get('TOKEN', '123456'))
GIT_REPOSITORY = settings.get('GIT_REPOSITORY_LIST', "https://github.com/Mxmilu666/bangbang93HUB")
GIT_REPOSITORY_LIST = GIT_REPOSITORY.split(",")
CERTIFICATES_STATUS = settings.get('CERTIFICATES', 'False').lower()

if ACCESS_LOG_CONTENT == 'true':
    ACCESS_LOG = True
elif ACCESS_LOG_CONTENT == 'false':
    ACCESS_LOG = False
else:
    logger.error(f"ACCESS_LOG 的值不正确，请修改为 true 或 false。")
    sys.exit(1)

if CERTIFICATES_STATUS == 'true':
    CERT_PATH = settings.get('CERT_PATH', '')
    KEY_PATH = settings.get('KEY_PATH', '')

# # 获取证书与密钥相关内容
# if CERTIFICATES_STATUS == True:
#     with open(CERT_PATH, "r", encoding="utf-8") as cert_file:
#         CERT = cert_file.read().strip()

#     with open(KEY_PATH, "r", encoding="utf-8") as key_file:
#         KEY = cert_file.read().strip()