import aiohttp
import socketio

import aiohttp
from aiohttp import web

from aiohttp_cors import setup, ResourceOptions
from core.mdb import fdb
from core.config import config


app = web.Application()
routes = web.RouteTableDef()

cors = setup(  
    app,
    defaults={
        "*": ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        ),
    },
)
filelist = []
async def fetch_filelist():
    global filelist
    async with aiohttp.ClientSession() as session:
        resp_json = await session.get('https://mod.mcimirror.top/file_cdn/list').json()
        filelist = resp_json

async def write_to_database(path: str,mtime: int,size: int,url: str):
    fdb.insert_one({
        "path": path,
        "mtime": mtime,
        "size": size,
        "url": url
    })
import avro.schema
from avro.datafile import DataFileWriter
from avro.io import DatumWriter

async def generate_avro_filelist():
    """
    生成符合 Avro schema 的文件列表并写入文件。
    """

    await fetch_filelist()
    schema = avro.schema.Parse("""
    {
      "type": "record",
      "name": "FileListEntry",
      "fields": [
        {"name": "path", "type": "string"},
        {"name": "hash", "type": "string"},
        {"name": "size", "type": "long"},
        {"name": "mtime", "type": "long"}
      ]
    }
    """)

    with open('filelist.avro', 'wb') as out:
        writer = DataFileWriter(out, DatumWriter(), schema)
        

        for entry in filelist:
            avro_record = {
                "path": entry['path'],
                "hash": entry.get('_id', ''),  # 如果文件列表中没有 hash 字段，则默认为空字符串
                "size": entry['size'],
                "mtime": entry['mtime']
            }
            writer.append(avro_record)
        writer.close()
async def init():
    for i in filelist:
        fdb.insert_one({
            
        })
    @routes.get('/files/mcim/{path}')
    async def _(path: str):
        data = fdb.find_one({"path": path})
        if data:
            return web.HTTPFound(data['url'])
        if not data:
            return web.HTTPNotFound()