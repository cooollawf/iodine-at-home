from pathlib import Path
import core.datafile as datafile

async def create_cluster(name: str, id: str, secret: str, bandwidth: int, trust: int = 0, isBanned: bool = False, banreason: str = '', host: str = '', port: int = 80, version: str = '', runtime: str = ''):
    data = await datafile.read_json_from_file("CLUSTER_LIST.json")
    data[id] = {
        'CLUSTER_NAME': name,
        'CLUSTER_ID': id,
        'CLUSTER_SECRET': secret,
        'CLUSTER_BANDWIDTH': bandwidth,
        'CLUSTER_TRUST': trust,
        'CLUSTER_ISBANNED': isBanned,
        'CLUSTER_BANREASON': banreason,
        'CLUSTER_HOST': host,
        'CLUSTER_PORT': port,
        'CLUSTER_VERSION': version,
        'CLUSTER_RUNTIME': runtime
    }
    await datafile.write_json_to_file("CLUSTER_LIST.json", data)
    return True

async def delete_cluster(id: str):
    data = await datafile.read_json_from_file("CLUSTER_LIST.json")
    if id in data:
        del data[id]
        await datafile.write_json_to_file("CLUSTER_LIST.json", data)
        return True
    else:
        return False

async def query_cluster_data(id: str):
    data = await datafile.read_json_from_file("CLUSTER_LIST.json")
    return data.get(id, False)

async def edit_cluster(id: str, name: str = None, secret: str = None, bandwidth: int = None, trust: int = None, isBanned: bool = None, ban_reason: str = None, host: str = None, port: int = None, version: str = None, runtime: str = None):
    data = await datafile.read_json_from_file("CLUSTER_LIST.json")

    if id in data:
        # 更新字段仅在提供时进行
        # 这段好屎山啊
        if name is not None:
            data[id]['CLUSTER_NAME'] = name
        if secret is not None:
            data[id]['CLUSTER_SECRET'] = secret
        if bandwidth is not None:
            data[id]['CLUSTER_BANDWIDTH'] = bandwidth
        if trust is not None:
            data[id]['CLUSTER_TRUST'] = trust
        if isBanned is not None:
            data[id]['CLUSTER_ISBANNED'] = isBanned
        if ban_reason is not None:
            data[id]['CLUSTER_BANREASON'] = ban_reason
        if host is not None:
            data[id]['CLUSTER_HOST'] = host
        if port is not None:
            data[id]['CLUSTER_PORT'] = port
        if version is not None:
            data[id]['CLUSTER_VERSION'] = version
        if runtime is not None:
            data[id]['CLUSTER_RUNTIME'] = runtime

        await datafile.write_json_to_file("CLUSTER_LIST.json", data)
        return True
    else:
        return False
