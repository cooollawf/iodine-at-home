import core.database as database

class Cluster:
    def __init__(self, id: str):
        if database.query_cluster_data(id).any().any():
            self.id = str(id)
            self.secret = str(database.query_cluster_data(id)["CLUSTER_SECRET"].item())
        else:
            return False
            
class FileObject:
    def __init__(self, path: str, hash: str, size: int, mtime: int):
        self.path = path
        self.hash = hash
        self.size = size
        self.mtime = mtime