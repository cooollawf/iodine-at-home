import os
import hmac
import time
import hashlib
import uvicorn
from typing import Any
from pathlib import Path
from pydantic import BaseModel
from fastapi import FastAPI, Header, Response, status, Request, Form
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
        return {"challenge": utils.encode_jwt({'cluster_id': clusterId, 'cluster_secret': database.query_cluster_data(clusterId)["CLUSTER_SECRET"].item(), "exp": int(time.time()) + 1000 * 60 * 5})}
    else:
        return PlainTextResponse("Not Found", 404)

# 获取 token 部分
@app.post("/openbmclapi-agent/token")
async def read_token(clusterId: str = Form(...), challenge: str = Form(...), signature: str = Form(...)):
    h = hmac.new(str(database.query_cluster_data(clusterId)["CLUSTER_SECRET"].item()).encode('utf-8'), digestmod=hashlib.sha256)
    h.update(challenge.encode())
    if database.query_cluster_data(clusterId).any().any() and utils.decode_jwt(challenge)["cluster_id"] == clusterId and utils.decode_jwt(challenge)["exp"] > int(time.time()):
        if str(h.hexdigest()) == signature:
            return {"token": utils.encode_jwt({'cluster_id': clusterId, 'cluster_secret': database.query_cluster_data(clusterId)["CLUSTER_SECRET"].item()}), "ttl": 1000 * 60 * 60 * 24}
        else:
            return PlainTextResponse("Unauthorized", 401)
    else:
        return PlainTextResponse("Unauthorized", 401)

def init():
    data_folder_path = Path('./data/')
    # 检查文件夹是否存在
    if not os.path.exists(data_folder_path):
        os.makedirs(data_folder_path)
    logger.info(f'加载中...')
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)