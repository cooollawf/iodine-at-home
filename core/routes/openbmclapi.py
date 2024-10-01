# 第三方库
import pyzstd
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse

# 本地库
from core.types import Avro
from core.logger import logger
from core.filesdb import FilesDB


app = APIRouter()


@app.get("/configuration", summary="同步参数", tags=["nodes"])  # 同步参数
def get_configuration(response: Response):
    # TODO: 根据当前负载情况智能调整并发数
    return {"sync": {"source": "center", "concurrency": 1024}}


@app.get("/files", summary="文件列表", tags=["nodes"])
async def get_filesList():
    logger.info("收到请求")
    async with FilesDB() as filesdb:
        filelist = filesdb.get_all()
    logger.info("获取文件列表成功")
    avro = Avro()
    avro.writeVarInt(len(filelist))  # 写入文件数量
    for file in filelist:
        avro.writeString(f"/{file['SOURCE']}/{file['HASH']}")  # 路径
        avro.writeString(file['HASH'])  # 哈希
        avro.writeVarInt(file['SIZE'])  # 文件大小
        avro.writeVarInt(file['MTIME'])  # 修改时间
    avro.write(b"\x00")
    result = pyzstd.compress(avro.io.getvalue())
    avro.io.close()
    logger.info("转码、压缩成功")
    return HTMLResponse(content=result, media_type="application/octet-stream")


@app.get("/download/{hash}", summary="应急同步", tags=["nodes"])
async def download_file_from_ctrl(hash: str):
    raise HTTPException(404, detail="未找到该文件")


@app.post("/report", summary="上报异常", tags=["nodes"])
async def post_report(request: Request):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        data = await request.json()
    elif "application/x-www-form-urlencoded" in content_type:
        data = await request.form()
        data = dict(data)
    elif "multipart/form-data" in content_type:
        data = await request.form()
        data = dict(data)
    else:
        raise HTTPException(status_code=400, detail="不支持的媒体类型")
    urls = data.get("urls")
    error = data.get("error")
    logger.warning(f"收到举报, 重定向记录: {urls}，错误信息: {error}")
    return Response(content="举报成功", status_code=200)
