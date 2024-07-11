import os
import sys
import yaml
import httpx
from loguru import logger

currentPath = os.path.dirname(os.path.realpath(__file__))
configPath = os.path.join(currentPath, 'config.yml')

# 尝试打开并读取配置文件
try:
    with open(configPath, 'r', encoding='UTF8') as cfgFile:
        config = yaml.safe_load(cfgFile)
except FileNotFoundError:
    logger.info("即将创建配置文件，创建过程结束后，服务将自动关闭，请前去配置。")
    try:
        response = httpx.get('https://jsd.onmicrosoft.cn/gh/Zero-Octagon/iodine-at-home@main/config.yml.example')
        if response.status_code == 200:
            # 打开一个本地文件以写入二进制数据
            with open(configPath, 'w') as cfgFile:
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
except yaml.YAMLError as exc:
    logger.error(f"配置文件中出现错误，报错信息: {exc}")
    sys.exit(1)

HOST = str(config.get('host', '0.0.0.0'))
PORT = int(config.get('port', 8080))
JWT_SECRET = str(config.get('jwt_secret', '114514'))