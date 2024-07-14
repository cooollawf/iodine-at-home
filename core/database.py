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
    })
    table = pa.Table.from_pandas(data)
    feather.write_feather(table, Path('./data/CLUSTER_LIST.feather'))

def new_cluster(name: str, id: str, secret: str, bandwidth: int):
    existing_data = pd.read_feather(Path('./data/CLUSTER_LIST.feather'))
    data = pd.DataFrame({
        'CLUSTER_NAME': [name],
        'CLUSTER_ID': [id],
        'CLUSTER_SECRET': [secret],
        'CLUSTER_BANDWIDTH': [bandwidth],
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