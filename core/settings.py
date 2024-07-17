import os
import sys
import yaml
import httpx
from loguru import logger
from dotenv import load_dotenv
from dotenv import dotenv_values

currentPath = os.path.dirname(os.path.realpath(__file__))
dotenvPath = os.path.join(currentPath, '../settings/.env')

# 尝试打开配置文件
env_status = load_dotenv(dotenvPath)

if env_status == False:
    logger.info("配置文件缺失，已创建空白文件。")
    with open(dotenvPath, 'w') as cfgFile:
        cfgFile.write('')
    logger.success(f"空白文件新建成功，请将 .env.example 内所有内容复制进 .env 并修改后运行程序。")
    sys.exit(0)

# 读取配置文件信息
settings = dotenv_values(dotenvPath)
HOST = str(settings.get('HOST', '0.0.0.0'))
PORT = int(settings.get('PORT', 8080))
JWT_SECRET = str(settings.get('JWT_SECRET', '114514'))