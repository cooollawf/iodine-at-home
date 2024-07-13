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
    logger.info("即将创建配置文件，创建后，程序将自动关闭，请前去配置。")
    try:
        response = httpx.get('https://jsd.onmicrosoft.cn/gh/Zero-Octagon/iodine-at-home@main/.env.example')
        if response.status_code == 200:
            # 打开一个本地文件以写入二进制数据
            with open(dotenvPath, 'w') as cfgFile:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        cfgFile.write(chunk)
            logger.success(f"远程配置文件保存成功。")
        else:
            logger.error("无法从远程服务器获取配置文件，可能是远程服务器暂不可用或流量过大造成的，请稍后再试。")
    except Exception as e:
        logger.error("无法从远程服务器获取配置文件，请检查网络连接。")
        sys.exit(1)
    sys.exit(0)

# 读取配置文件信息
settings = dotenv_values(dotenvPath)
HOST = str(settings.get('HOST', '0.0.0.0'))
PORT = int(settings.get('PORT', 8080))
JWT_SECRET = str(settings.get('JWT_SECRET', '114514'))