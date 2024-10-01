# 第三方库
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import FileResponse, RedirectResponse

# 本地库
from core.logger import logger
from core.filesdb import FilesDB

app = APIRouter()


@app.get("/files/{path}", summary="下载普通文件", tags=["public"])
async def download_file(path: str):
    async with FilesDB() as filesdb:
        filedata = filesdb.find_one(path)
    if filedata:
        return RedirectResponse(filedata["path"], 302)
    else:
        raise HTTPException(404, detail="未找到该文件")
