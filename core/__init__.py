# 第三方库
import socketio

import aiohttp
from aiohttp import web
from aiohttp.web import Request

from aiohttp_cors import setup, ResourceOptions

# 自定义库
from core.config import config

# 全局变量
## 网页部分
app = web.Application()
routes = web.RouteTableDef()

cors = setup(  # CORS 设置
    app,
    defaults={
        "*": ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        ),
        "/socket.io/": ResourceOptions(  # 明确指定 SocketIO 不使用 CORS
            allow_credentials=False,
            expose_headers="*",
            allow_headers="*",
            max_age=3600,
        ),
    },
)

## SocketIO 部分
sio = socketio.AsyncServer(async_mode="aiohttp")
sio.attach(app)  # 将 SocketIO 附加到网页服务中

# 核心功能
## 节点验证时下发 challenge（有效期: 5分钟）
@routes.get("/openbmclapi-agent/challenge")
async def get_challenge(request: Request):
    print(11)

## 建议同步参数
@routes.get("/openbmclapi/configuration")
def fetch_configuration(request: Request):
    ## TODO: 根据当前负载情况智能调整并发数
    return web.json_response({"sync": {"source": "center", "concurrency": 1024}})

def init():
    web.run_app(app, host=config.get("web.host"), port=config.get("web.port"))