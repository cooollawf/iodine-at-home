# import json
# import httpx
# import core.datafile as datafile

# def fetch_all_data():
#     url = "https://mod.mcimirror.top/file_cdn/list"
#     all_data = []
#     last_id = 0

#     zhanyongkongjian = 0

#     while True:
#         params = {
#             "last_id": last_id,
#             "page_size": 9999
#         }
#         response = httpx.get(url, params=params, timeout=1000)
#         data = json.loads(response.text)  # 假设

#         if not data:
#             break

#         all_data.extend(data)
#         last_id = data[-1]["_id"]  # 假设每条数据都有一个"id"字段
#         last_modified = data[-1]["mtime"]  # 假设每条数据都有一个"modified"字段
#         for i in data:
#             zhanyongkongjian += i["size"]
#         print(len(all_data))
#         print(f'占用空间 {zhanyongkongjian}')
#     return all_data

# # 使用函数获取所有数据
# all_data = fetch_all_data()
# datafile.write_json_to_file_noasync('mcim.json', all_data)
# print(f"数据总数 {len(all_data)}")  # 打印获取到的数据总数

import asyncio
import aiohttp

async def fetch_93_home():
    headers = {"User-Agent": f"mxmilu666-dick/40cm"}
    async with aiohttp.ClientSession() as client:
        resp = await client.get("http://home.5k.work:15105/files/93hub/[bangbang%E5%A5%B3%E8%A3%85]%E5%8F%AF%E4%BB%A5%E7%BB%99%E5%85%B6%E4%BB%96%E7%BE%A4%E4%B8%BB%E6%96%BD%E5%8E%8B.png", headers=headers, timeout=10)
    if resp.status == 200:
        print("OK!")

while True:
    asyncio.run(fetch_93_home())