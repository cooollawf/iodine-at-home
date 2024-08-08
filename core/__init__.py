import os
import re
import json
import hmac
import time
import hashlib
import asyncio
from pathlib import Path
from random import choice
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Header, Response, status, Request, Form
from fastapi.responses import PlainTextResponse, RedirectResponse, FileResponse, HTMLResponse
import uvicorn.config

import core.utils as utils
from core.logger import logger
import core.datafile as datafile
import core.database as database
import core.settings as settings
import core.const
from core.upstream import Upstream
from core.types import Cluster, FileObject

from starlette.routing import Mount
from starlette.applications import Starlette
from socketio.asgi import ASGIApp
from socketio.async_server import AsyncServer

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 初始化变量
app = FastAPI()
sio = AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket = ASGIApp(sio)
enable_cluster_list = []
upstream = Upstream("https://github.com/Mxmilu666/bangbang93HUB", "./files")

# 定时执行
scheduler = BackgroundScheduler()
scheduler.add_job(utils.save_calculate_filelist, 'interval', minutes=10, id='refresh_filelist')

# 以 JSON 格式返回节点列表
@app.get("/iodine/cluster-list")
async def fetch_cluster_list(response: Response, token: str | None):
    if token != settings.TOKEN:
        return PlainTextResponse("没有权限", 401)
    return await datafile.read_json_from_file("CLUSTER_LIST.json")

# 执行命令（很容易爆炸！！！）
@app.get("/iodine/delete")
async def fetch_cmd(response: Response, token: str | None):
    if token != settings.TOKEN:
        return PlainTextResponse("没有权限", 401)
    return await database.query_cluster_data("114514")

@app.get("/iodine/update")
async def update_files(token : str) -> Response:
    if token != settings.TOKEN:
        return PlainTextResponse("没有权限", 401)
    def update():
        upstream.fetch()
        utils.save_calculate_filelist()
    if scheduler.get_job(job_id='update_files') is not None:
        return PlainTextResponse(core.const.conflict_response, 409)
    job = scheduler.add_job(update, id='update_files')
    return PlainTextResponse(status_code=204)
    
    
# 下发 challenge（有效时间: 5 分钟）
@app.get("/openbmclapi-agent/challenge")
async def fetch_challenge(response: Response, clusterId: str | None = ""):
    cluster = Cluster(clusterId)
    cluster_is_exist = await cluster.initialize()
    if cluster_is_exist and cluster.isBanned == 0:
        return {"challenge": utils.encode_jwt({'cluster_id': clusterId, 'cluster_secret': cluster.secret, "exp": int(time.time()) + 1000 * 60 * 5})}
    elif cluster_is_exist and cluster.isBanned == True:
        return PlainTextResponse(f"节点被封禁，原因: {cluster.ban_reason}", 403)
    else:
        return PlainTextResponse("节点未找到", 404)

# 下发令牌（有效日期: 1 天）
@app.post("/openbmclapi-agent/token")
async def fetch_token(request: Request, resoponse: Response):
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        data = await request.form()
    clusterId = data.get("clusterId")
    challenge = data.get("challenge")
    signature = data.get("signature")
    cluster = Cluster(clusterId)
    cluster_is_exist = await cluster.initialize()
    h = hmac.new(cluster.secret.encode('utf-8'), digestmod=hashlib.sha256)
    h.update(challenge.encode())
    if cluster_is_exist and utils.decode_jwt(challenge)["cluster_id"] == clusterId and utils.decode_jwt(challenge)["exp"] > int(time.time()):
        if str(h.hexdigest()) == signature:
            return {"token": utils.encode_jwt({'cluster_id': clusterId, 'cluster_secret': cluster.secret}), "ttl": 1000 * 60 * 60 * 24}
        else:
            return PlainTextResponse("没有授权", 401)
    else:
        return PlainTextResponse("没有授权", 401)
    
# 建议同步参数
@app.get("/openbmclapi/configuration")
def fetch_configuration():
    return {"sync": {"source": "center", "concurrency": 100}}

# 文件列表
@app.get("/openbmclapi/files")
async def fetch_filesList():
    # TODO: 获取文件列表
    filelist = await datafile.read_filelist_from_cache("filelist.avro")
    return HTMLResponse(content=filelist, media_type="application/octet-stream")

# 普通下载（从主控或节点拉取文件）
@app.get("/files/{path:path}")
async def download_file(path: str):
    if Path(f"./files/{path}").is_file() == False:
        return PlainTextResponse("Not Found", 404)
    if Path(f"./files/{path}").is_dir == True:
        return PlainTextResponse("Not Found", 404)
    if len(enable_cluster_list) == 0:
        return FileResponse(f"./files/{path}")
    else:
        cluster = choice(enable_cluster_list)
        file = FileObject(f"./files/{path}")
        url = utils.get_url(cluster["host"], cluster["port"], f"/download/{file.hash}", utils.get_sign(file.hash, cluster["secret"])) 
        return RedirectResponse(url, 302)

# 应急同步（从主控拉取文件）
@app.get("/openbmclapi/download/{hash}")
def download_file(hash: str):
    return FileResponse(utils.hash_file(Path(f'./files/{hash}')))

# 举报
@app.post("/openbmclapi/report")
async def fetch_report(request: Request):
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        data = await request.form()
    urls = data.get("urls")
    error = data.get("error")
    logger.warning(f"收到举报, 重定向记录: {urls}，错误信息: {error}")
    return Response(status_code=200)

# 节点端连接时
@sio.on('connect')
async def on_connect(sid, *args):
    token_pattern = r"'token': '(.*?)'"
    token = re.search(token_pattern, str(args)).group(1)
    if token.isspace():
        sio.disconnect(sid)
        logger.info(f"客户端 {sid} 连接失败（原因: 未提交 token 令牌）")
    cluster = Cluster(utils.decode_jwt(token)["cluster_id"])
    cluster_is_exist = await cluster.initialize()
    if cluster_is_exist and cluster.secret == utils.decode_jwt(token)['cluster_secret']:
        await sio.save_session(sid, {"cluster_id": cluster.id, "cluster_secret": cluster.secret, "token": token})
        logger.info(f"客户端 {sid} 连接成功（CLUSTER_ID: {cluster.id}）")
    else:
        sio.disconnect(sid)
        logger.info(f"客户端 {sid} 连接失败（原因: 认证出错）")

# 当节点端退出连接时
@sio.on('disconnect')
async def on_disconnect(sid, *args):
    session = await sio.get_session(sid)
    cluster = Cluster(str(session['cluster_id']))
    cluster_is_exist = await cluster.initialize()
    if cluster_is_exist and cluster.json() in enable_cluster_list:
        enable_cluster_list.remove(cluster.json())
        logger.info(f"{sid} 异常断开连接，已从在线列表中删除")
    else:
        logger.info(f"客户端 {sid} 关闭了连接")

# 节点启动时
@sio.on('enable')
async def on_cluster_enable(sid, data, *args):
    session = await sio.get_session(sid)
    cluster = Cluster(str(session['cluster_id']))
    cluster_is_exist = await cluster.initialize()
    if cluster_is_exist == False:
        return [{"message": f"错误: 节点似乎并不存在，请检查配置文件"}]
    logger.info(f"{sid} 申请启用（CLUSTER_ID: {session['cluster_id']}）")
    host = data.get("host", session.get("ip"))
    await cluster.edit(host = host, port = data["port"], version = data["version"], runtime = data["flavor"]["runtime"])
    time.sleep(1)
    bandwidth = await utils.measure_cluster(10, cluster.json())
    if bandwidth[0] and bandwidth[1] >= 10:
        enable_cluster_list.append(cluster.json())
        logger.info(f"{sid} 上线成功（测量带宽: {bandwidth[1]}）")
        # utils.choose_file()
        return [None, True]
    elif bandwidth[0] and bandwidth[1] < 10:
        logger.info(f"{sid} 测速未通过（测量带宽: {bandwidth[1]}）")
        return [{"message": f"错误: 测量带宽小于 10Mbps，（测量得{bandwidth[1]}），请重试尝试上线"}]
    else:
        logger.info(f"{sid} 测速未通过（测量带宽: {bandwidth[1]}）")
        return [{"message": f"错误: {bandwidth[1]}"}]

# 节点保活时
@sio.on('keep-alive')
async def on_cluster_keep_alive(sid, data, *args):
    logger.info(f"{sid} 保活（请求数: {data['hits']} 次 | 请求数据量: {utils.hum_convert(data['bytes'])}）")
    return [None, datetime.now(timezone.utc).isoformat()]
    # return [None, False]

# 节点禁用时
@sio.on('disable')
async def on_cluster_disable(sid, *args):
    logger.info(f"{sid} 申请禁用集群")
    session = await sio.get_session(sid)
    cluster = Cluster(str(session['cluster_id']))
    await cluster.initialize()
    try:
        enable_cluster_list.remove(cluster.json())
        logger.info(f"{sid} 尝试禁用集群")
    except ValueError:
        logger.info(f"{sid} 尝试禁用集群失败（原因: 节点没有启用）")
    return [None, True]


def init():
    # 检查文件夹是否存在
    if not os.path.exists(Path('./data/')):
        os.makedirs(Path('./data/'))
    if not os.path.exists(Path('./files/')):
        os.makedirs(Path('./files/'))
    logger.info(f'加载中...')
    Upstream("https://gh.con.sh/https://github.com/Mxmilu666/bangbang93HUB", "./files/bangbang93HUB").fetch()
    utils.save_calculate_filelist()
    app.mount('/', socket)
    try:
        scheduler.start()
        uvicorn.run(app, host=settings.HOST, port=settings.PORT, access_log=False)
    except KeyboardInterrupt:
        scheduler.shutdown()
        logger.info('主控已经成功关闭。')



#              这是一只一只一只 屎山大佛
#
#                      _oo0oo_
#                     o8888888o
#                     88" . "88
#                     (| -_- |)
#                     0\  =  /0
#                   ___/`---'\___
#                 .' \\|     |// '.
#                / \\|||  :  |||// \
#               / _||||| -:- |||||- \
#              |   | \\\  - /// |   |
#              | \_|  ''\---/''  |_/ |
#              \  .-\__  '-'  ___/-. /
#             ___'. .'  /--.--\  `. .'___
#         ."" '<  `.___\_<|>_/___.' >' "".
#        | | :  `- \`.;`\ _ /`;.`/ - ` : | |
#        \  \ `_.   \_ __\ /__ _/   .-` /  /
#    =====`-.____`.___ \_____/___.-`___.-'=====
#                      `=---='
#
#
#    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
#       佛祖保佑         永不宕机        永无BUG
#
#
#         佛曰:
#             写字楼里写字间，写字间里程序员；
#             程序人员写程序，又拿程序换酒钱。
#             酒醒只在网上坐，酒醉还来网下眠；
#             酒醉酒醒日复日，网上网下年复年。
#             但愿老死电脑间，不愿鞠躬老板前；
#             奔驰宝马贵者趣，公交自行程序员。
#             别人笑我忒疯癫，我笑自己命太贱；
#             不见满街漂亮妹，哪个归得程序员？
#             君子出生在墙内，并非君子之错也.
#
#                        来自 ZeroWolf233  2024.7.30 10:51