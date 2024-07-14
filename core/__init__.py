import os
import time
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Response, status
from fastapi.responses import PlainTextResponse, RedirectResponse

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
        return {"challenge": utils.generate_jwt_token({'cluster_id': clusterId, 'cluster_secret': '8cc82781b5c0e2631f96fb96d9f7f48c', "exp": int(time.time()) + 60 * 5 * 24 * 1})}

def init():
    data_folder_path = Path('./data/')
    # 检查文件夹是否存在
    if not os.path.exists(data_folder_path):
        os.makedirs(data_folder_path)
    logger.info(f'加载中...')
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)