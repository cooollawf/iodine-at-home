import jwt
import time
import uvicorn
from loguru import logger
from fastapi import FastAPI, Response, status
from fastapi.responses import PlainTextResponse

import config
import utils

# 初始化变量
app = FastAPI()

# 获取 challenge 部分
@app.get("/openbmclapi-agent/challenge")
def read_challenge(response: Response, clusterId: str | None = ''):
    challenge = '111'
    if clusterId == '':
        return PlainTextResponse("Not Found", 404)
    else:
        return {"challenge": utils.generate_jwt_token({'clusterId': clusterId, "exp": int(time.time()) + 60 * 60 * 24 * 1})}

# 启动 uvicorn 服务器
if __name__ == '__main__':
    try:
        logger.info("服务启动中...")
        uvicorn.run(app, host=config.HOST, port=config.PORT)
    except KeyboardInterrupt:
        logger.info("服务正在关闭中...")