import pandas as pd
import pyarrow as pa
from pathlib import Path
import pyarrow.feather as feather
def create_cluster_list():
    data = pd.DataFrame({
        'CLUSTER_NAME': [],
        'CLUSTER_ID': [],
        'CLUSTER_SECRET': [],
        'CLUSTER_BANDWIDTH': [],
        'CLUSTER_TRUST':[],
        'CLUSTER_ISBANNED':[],
        'CLUSTER_BANREASON':[],
    })
    table = pa.Table.from_pandas(data)
    feather.write_feather(table, Path('./data/CLUSTER_LIST.feather'))

def new_cluster(name: str, id: str, secret: str, bandwidth: int, trust: int = 0, isBanned: int = 0, ban_reason: str = ''):
    existing_data = pd.read_feather(Path('./data/CLUSTER_LIST.feather'))
    data = pd.DataFrame({
        'CLUSTER_NAME': [name],
        'CLUSTER_ID': [id],
        'CLUSTER_SECRET': [secret],
        'CLUSTER_BANDWIDTH': [bandwidth],
        'CLUSTER_TRUST':[trust],
        'CLUSTER_ISBANNED':[isBanned],
        'CLUSTER_BANREASON':[ban_reason],
    })
    data_appended = pd.concat([existing_data, data], ignore_index=True)
    feather.write_feather(data_appended, Path('./data/CLUSTER_LIST.feather'))

def remove_cluster(id: str):
    try:
        existing_data = pd.read_feather(Path('./data/CLUSTER_LIST.feather'))
        data_deleted = existing_data.drop(existing_data[existing_data['CLUSTER_ID'] == id].index)
        feather.write_feather(data_deleted, Path('./data/CLUSTER_LIST.feather'))
        return 'OK'
    except KeyError:
        return None

def query_cluster_data(id: str):
    existing_data = pd.read_feather(Path('./data/CLUSTER_LIST.feather'))
    result = existing_data[existing_data['CLUSTER_ID'] == id]
    return result

def update_cluster(id: str, name: str = None, secret: str = None, bandwidth: int = None, trust: int = None, is_banned: int = None, ban_reason: str = None):
    existing_data = pd.read_feather(Path('./data/CLUSTER_LIST.feather'))
    
    # 查找需要更新的行
    row_to_update = existing_data.loc[existing_data['CLUSTER_ID'] == id]

    if not row_to_update.empty:
        # 创建一个字典来存储更新的字段
        updates = {}
        if name is not None:
            updates['CLUSTER_NAME'] = name
        if secret is not None:
            updates['CLUSTER_SECRET'] = secret
        if bandwidth is not None:
            updates['CLUSTER_BANDWIDTH'] = bandwidth
        if trust is not None:
            updates['CLUSTER_TRUST'] = trust
        if is_banned is not None:
            updates['CLUSTER_ISBANNED'] = is_banned
        if ban_reason is not None:
            updates['CLUSTER_BANREASON'] = ban_reason

        # 如果有更新的字段，则更新数据
        if updates:
            existing_data.update(pd.DataFrame(updates, index=row_to_update.index))

        # 将更新后的 DataFrame 写回文件
        feather.write_feather(existing_data, Path('./data/CLUSTER_LIST.feather'))
        return True
    else:
        return False
    
def feather_to_html():
    existing_data = pd.read_feather(Path('./data/CLUSTER_LIST.feather'))
    return existing_data.to_html()