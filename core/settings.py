import os
import sys
import yaml
import httpx
from pathlib import Path
from loguru import logger
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
JWT_SECRET = str(settings.get('JWT_SECRET', '114514'))