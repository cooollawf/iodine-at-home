import os
import re
import hmac
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Header, Response, status, Request, Form
from fastapi.responses import PlainTextResponse, RedirectResponse, FileResponse, HTMLResponse
import uvicorn.config

import core.utils as utils
import core.database as database
import core.settings as settings
from core.utils import logging as logger
from core.types import Cluster, FileObject

from starlette.routing import Mount
from starlette.applications import Starlette
from socketio.asgi import ASGIApp
from socketio.async_server import AsyncServer

# 初始化变量
app = FastAPI()
sio = AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket = ASGIApp(sio)

# 节点列表 HTML 界面
@app.get("/iodine/cluster-list")
def fetch_cluster_list(response: Response):
    return HTMLResponse(database.feather_to_html())

# 执行命令（高危！！！）
@app.get("/iodine/cmd")
def fetch_cluster_list(response: Response, command: str | None = ""):
    return exec(command)
    
# 下发 challenge（有效期: 5 分钟）
@app.get("/openbmclapi-agent/challenge")
def fetch_challenge(response: Response, clusterId: str | None = ""):
    cluster = Cluster(clusterId)
    if cluster and cluster.isBanned == 0:
        return {"challenge": utils.encode_jwt({'cluster_id': clusterId, 'cluster_secret': cluster.secret, "exp": int(time.time()) + 1000 * 60 * 5})}
    elif cluster and cluster.isBanned == 1:
        return PlainTextResponse(f"Your cluster has been banned for the following reasons: {cluster.ban_reason}", 403)
    else:
        return PlainTextResponse("Not Found", 404)

# 下发令牌（有效期: 1 天）
@app.post("/openbmclapi-agent/token")
async def fetch_token(resoponse: Response ,clusterId: str = Form(...), challenge: str = Form(...), signature: str = Form(...)):
    cluster = Cluster(clusterId)
    h = hmac.new(cluster.secret.encode('utf-8'), digestmod=hashlib.sha256)
    h.update(challenge.encode())
    if cluster and utils.decode_jwt(challenge)["cluster_id"] == clusterId and utils.decode_jwt(challenge)["exp"] > int(time.time()):
        if str(h.hexdigest()) == signature:
            return {"token": utils.encode_jwt({'cluster_id': clusterId, 'cluster_secret': cluster.secret}), "ttl": 1000 * 60 * 60 * 24}
        else:
            return PlainTextResponse("Unauthorized", 401)
    else:
        return PlainTextResponse("Unauthorized", 401)
    
# 建议同步参数
@app.get("/openbmclapi/configuration")
def fetch_configuration():
    return {"sync": {"source": "center", "concurrency": 100}}

# 文件列表
@app.get("/openbmclapi/files")
def fetch_filesList():
    # TODO: 获取文件列表
    return Response(content=utils.compute_avro_bytes(), media_type="application/octet-stream")

# 普通下载（从主控或节点拉取文件）
@app.get("/files/{path}")
def download_file(path: str):
    return PlainTextResponse(utils.hash_file(Path(f'./files/{path}')))

# 紧急同步（从主控拉取文件）
@app.get("/openbmclapi/download/{hash}")
def download_file(hash: str):
    return FileResponse(utils.hash_file(Path(f'./files/{hash}')))

# 节点端连接时
@sio.on('connect')
async def on_connect(sid, *args):
    token_pattern = r"'token': '(.*?)'"
    token = re.search(token_pattern, str(args)).group(1)
    cluster = Cluster(utils.decode_jwt(token)["cluster_id"])
    if cluster and cluster.secret == utils.decode_jwt(token)['cluster_secret']:
        await sio.save_session(sid, {"cluster_id": cluster.id, "cluster_secret": cluster.secret, "token": token})
        logger.info(f"客户端 {sid} 连接成功（CLUSTER_ID: {cluster.id}）")
    else:
        sio.disconnect(sid)
        logger.info(f"客户端 {sid} 连接失败（原因: 认证失败）")

# 节点端退出连接时
@sio.on('disconnect')
async def on_disconnect(sid, *args):
    logger.info(f"客户端 {sid} 关闭了连接")

# 节点启动时
@sio.on('enable')
async def on_cluster_enable(sid, data, *args):
    # TODO: 启动节点时的逻辑以及检查节点是否符合启动要求部分
    logger.info(f"{sid} 启用了集群（{data}）")
    # 成功: return [None, True]
    return [{"message":"把头低下！鼠雀之辈！啊哈哈哈哈！"}]

# 节点保活时
@sio.on('keep-alive')
async def on_cluster_keep_alive(sid, data, *args):
    # TODO: 当节点保活时检测节点是否正确上报数据
    logger.info(f"{sid} 保活（{data}）")
    # 成功: return [None, datetime.now(timezone.utc).isoformat()]
    return [None, False]

def init():
    # 检查文件夹是否存在
    if not os.path.exists(Path('./data/')):
        os.makedirs(Path('./data/'))
    if not os.path.exists(Path('./files/')):
        os.makedirs(Path('./files/'))
    logger.info(f'加载中...')
    app.mount('/', socket)
    try:
        uvicorn.run(app, host=settings.HOST, port=settings.PORT)
    except KeyboardInterrupt:
        logger.info('主控已关闭。')

# uvicorn.config.LOGGING_CONFIG = 