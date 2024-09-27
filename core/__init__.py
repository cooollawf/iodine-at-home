# 第三方库
import re
import time
import asyncio
import uvicorn
from pluginbase import PluginBase
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

import socketio
from socketio.asgi import ASGIApp

# 本地库
from core.mdb import cdb
import core.utils as utils
from core.logger import logger
from core.config import config
from core.types import Cluster

# 路由库
from core.routes.agent import app as agent_router
from core.routes.openbmclapi import app as openbmclapi_router
from core.routes.services import app as services_router

# 网页部分
app = FastAPI(
    title="iodine@home",
    summary="开源的文件分发主控，并尝试兼容 OpenBMCLAPI 客户端",
    version="2.0.0",
    license_info={
        "name": "The MIT License",
        "url": "https://raw.githubusercontent.com/ZeroNexis/iodine-at-home/main/LICENSE",
    },
)

app.include_router(agent_router, prefix="/openbmclapi-agent")
app.include_router(openbmclapi_router, prefix="/openbmclapi")
app.include_router(services_router)

## 跨域设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 插件部分
plugin_base = PluginBase(package="plugin")
plugin_source = plugin_base.make_plugin_source(searchpath=["./plugins"])


async def load_plugins():
    for plugin_name in plugin_source.list_plugins():
        logger.info(f"插件 {plugin_name} 加载中...")
        plugin = plugin_source.load_plugin(plugin_name)
        logger.info(f"插件「{plugin.__NAME__}」加载成功！")
        if hasattr(plugin, "__API__") and plugin.__API__:
            if hasattr(plugin, "app"):
                app.include_router(plugin.app, prefix=f"/{plugin.__NAMESPACE__}")
            else:
                logger.warning(
                    f"插件「{plugin.__NAME__}」未定义 App ，无法加载该插件的路径！"
                )
        await plugin.init()


# SocketIO 部分
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socket = ASGIApp(sio)

# 核心功能
online_cluster_list_json = []


## 节点端连接时
@sio.on("connect")
async def on_connect(sid, *args):
    token_pattern = r"'token': '(.*?)'"
    token = re.search(token_pattern, str(args)).group(1)
    if token.isspace():
        sio.disconnect(sid)
        logger.debug(f"客户端 {sid} 连接失败（原因: 未提交 token 令牌）")
    cluster = Cluster(utils.decode_jwt(token)["cluster_id"])
    if await cluster.initialize() == False:
        sio.disconnect(sid)
        logger.debug(f"客户端 {sid} 连接失败（原因: 集群 {cluster.id} 不存在）")
    if cluster.secret == utils.decode_jwt(token)["cluster_secret"]:
        await sio.save_session(
            sid,
            {
                "cluster_id": cluster.id,
                "cluster_secret": cluster.secret,
                "token": token,
            },
        )
        logger.debug(f"客户端 {sid} 连接成功（CLUSTER_ID: {cluster.id}）")
        await sio.emit(
            "message",
            "欢迎使用 iodine@home，本项目已在 https://github.com/ZeroNexis/iodine-at-home 开源，期待您的贡献与支持。",
            sid,
        )
    else:
        sio.disconnect(sid)
        logger.debug(f"客户端 {sid} 连接失败（原因: 认证出错）")


## 当节点端退出连接时
@sio.on("disconnect")
async def on_disconnect(sid, *args):
    session = await sio.get_session(sid)
    cluster = Cluster(str(session["cluster_id"]))
    cluster_is_exist = await cluster.initialize()
    if cluster_is_exist and cluster.json() in online_cluster_list_json:
        online_cluster_list_json.remove(cluster.json())
        logger.debug(f"{sid} 异常断开连接，已从在线列表中删除")
    else:
        logger.debug(f"客户端 {sid} 断开了连接")


def init():
    try:
        asyncio.run(load_plugins())
        app.mount("/", socket)
        logger.info(
            f"正在 {config.get('host')}:{config.get(path='port')} 上监听服务器..."
        )

        uvicorn.run(
            app,
            host=config.get("host"),
            port=config.get(path="port"),
            log_level="warning",
        )
    except KeyboardInterrupt:
        logger.info("主控已经成功关闭。")
