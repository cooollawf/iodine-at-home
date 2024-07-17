import os
import re
import zstd
import hmac
import time
import hashlib
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Header, Response, status, Request, Form
from fastapi.responses import PlainTextResponse, RedirectResponse

import core.utils as utils
import core.database as database
import core.settings as settings
from core.utils import logging as logger

from starlette.routing import Mount
from starlette.applications import Starlette
from socketio.asgi import ASGIApp
from socketio.async_server import AsyncServer

# 初始化变量
app = FastAPI()
sio = AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket = ASGIApp(sio)

# 获取 challenge 部分
@app.get("/openbmclapi-agent/challenge")
def fetch_challenge(response: Response, clusterId: str | None = ""):
    if database.query_cluster_data(clusterId).any().any():
        return {"challenge": utils.encode_jwt({'cluster_id': clusterId, 'cluster_secret': database.query_cluster_data(clusterId)["CLUSTER_SECRET"].item(), "exp": int(time.time()) + 1000 * 60 * 5})}
    else:
        return PlainTextResponse("Not Found", 404)

# 获取 token 部分
@app.post("/openbmclapi-agent/token")
async def fetch_token(clusterId: str = Form(...), challenge: str = Form(...), signature: str = Form(...)):
    h = hmac.new(str(database.query_cluster_data(clusterId)["CLUSTER_SECRET"].item()).encode('utf-8'), digestmod=hashlib.sha256)
    h.update(challenge.encode())
    if database.query_cluster_data(clusterId).any().any() and utils.decode_jwt(challenge)["cluster_id"] == clusterId and utils.decode_jwt(challenge)["exp"] > int(time.time()):
        if str(h.hexdigest()) == signature:
            return {"token": utils.encode_jwt({'cluster_id': clusterId, 'cluster_secret': database.query_cluster_data(clusterId)["CLUSTER_SECRET"].item()}), "ttl": 1000 * 60 * 60 * 24}
        else:
            return PlainTextResponse("Unauthorized", 401)
    else:
        return PlainTextResponse("Unauthorized", 401)
    
# 获取 token 部分
@app.get("/openbmclapi/configuration")
def fetch_configuration():
    return {"sync": {"source": "center", "concurrency": 100}}

# 获取 token 部分
@app.get("/openbmclapi/files")
def fetch_filesList():
    # TODO: 获取文件列表
    return {"message": "这还在做，你别催！"}

@sio.on('connect')
async def on_connect(sid, *args):
    token_pattern = r"'token': '(.*?)'"
    token = re.search(token_pattern, str(args)).group(1)
    database_data = database.query_cluster_data(utils.decode_jwt(token)["cluster_id"])
    if database_data.any().any() and database_data["CLUSTER_SECRET"].item() == utils.decode_jwt(token)['cluster_secret']:
        await sio.save_session(sid, {"cluster_id": database_data["CLUSTER_ID"].item(), "cluster_secret": database_data["CLUSTER_SECRET"].item(), "token": token})
        logger.info(f"客户端 {sid} 连接成功（CLUSTER_ID: {database_data['CLUSTER_ID'].item()}）")
    else:
        sio.disconnect(sid)
        logger.info(f"客户端 {sid} 连接失败（原因: 认证失败）")

@sio.on('enable')
async def on_cluster_enable(sid, *args):
    # TODO: 启动节点时的逻辑以及检查节点是否符合启动要求部分
    logger.info(f"{sid} 启用了集群")

def init():
    data_folder_path = Path('./data/')
    # 检查文件夹是否存在
    if not os.path.exists(data_folder_path):
        os.makedirs(data_folder_path)
    logger.info(f'加载中...')
    app.mount('/', socket)
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)