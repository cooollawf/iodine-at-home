import os
import time
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Response, status
from fastapi.responses import PlainTextResponse, RedirectResponse

import core.utils as utils
import core.database as database
import core.settings as settings
from core.utils import logging as logger

# 初始化变量
app = FastAPI()
# 获取 challenge 部分
@app.get("/openbmclapi-agent/challenge")
def read_challenge(response: Response, clusterId: str | None = ""):
    if database.query_cluster_data(clusterId).any().any():
        return {"challenge": utils.generate_jwt_token({'cluster_id': clusterId, 'cluster_secret': database.query_cluster_data(clusterId)["CLUSTER_SECRET"].item(), "exp": int(time.time()) + 60 * 5 * 24 * 1})}
    else:
        return PlainTextResponse("Not Found", 404)

def init():
    data_folder_path = Path('./data/')
    # 检查文件夹是否存在
    if not os.path.exists(data_folder_path):
        os.makedirs(data_folder_path)
    logger.info(f'加载中...')
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)