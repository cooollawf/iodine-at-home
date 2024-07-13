import time
import uvicorn
from fastapi import FastAPI, Response, status
from fastapi.responses import PlainTextResponse

import core.settings as settings
import core.utils as utils
from core.utils import logging as logger

# 初始化变量
app = FastAPI()
# 获取 challenge 部分
@app.get("/openbmclapi-agent/challenge")
def read_challenge(response: Response, clusterId: str | None = ''):
    if clusterId == '':
        return PlainTextResponse("Not Found", 404)
    else:
        return {"challenge": utils.generate_jwt_token({'clusterId': clusterId, "exp": int(time.time()) + 60 * 5 * 24 * 1})}

def init(py_version):
    logger.info(f'加载中...')
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)