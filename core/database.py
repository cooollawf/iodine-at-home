import asyncio
from aiosqlite import Cursor
from pathlib import Path
import motor.motor_asyncio
import core.datafile as datafile
import core.settings as settings


class Database:
    def __init__(
        self,
        host: str,
        db_name: str,
        collection_name: str,
        username=None,
        password=None,
    ):
        uri = (
            f"mongodb://{username}:{password or ''}@{host}/"
            if username
            else f"mongodb://{host}/"
        )
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.collection_name = collection_name

    async def close(self):
        self.client.close()

    async def collection(self, collection_name: str):
        return self.db[collection_name]

    async def insert_one(self, cluster_data: dict):
        collection = await self.collection(self.collection_name)
        result = await collection.insert_one(cluster_data)
        return result.inserted_id

    async def create_cluster(
        self,
        name: str = None,
        secret: str = None,
        bandwidth: int = None,
    ):
        return await self.insert_one(
            {
                "name": name,
                "secret": secret,
                "bandwidth": bandwidth,
            }
        )

    async def delete_cluster(self, id: str):
        collection = await self.collection(self.collection_name)
        await collection.delete_one({"_id": id})

    async def find_cluster(self, id: str):
        collection = await self.collection(self.collection_name)
        result = await collection.find_one({"_id": id})
        if result:
            return [True,result]
        return [False,None]

    async def update_cluster(self, id: str, update_data: dict):
        collection = await self.collection(self.collection_name)
        await collection.update_one({"_id": id}, {"$set": update_data})

    async def get_clusters(self):
        collection = await self.collection(self.collection_name)
        cursor = collection.find()
        return [doc async for doc in cursor]

    async def edit_cluster(
        self,
        id: str,
        name: str = None,
        secret: str = None,
        bandwidth: int = None,
        trust: int = None,
        isBanned: bool = None,
        ban_reason: str = None,
        host: str = None,
        port: int = None,
        version: str = None,
        runtime: str = None,
    ):
        result = await self.db.clusters.update_one(
            {"_id": id},
            {
                "$set": {
                    "name": name,
                    "secret": secret,
                    "bandwidth": bandwidth,
                    "trust": trust,
                    "isBanned": isBanned,
                    "ban_reason": ban_reason,
                    "host": host,
                    "port": port,
                    "version": version,
                    "runtime": runtime,
                }
            },
        )
        if result.modified_count == 1:
            return True
        return False


database = Database(
    settings.MDB_HOST,
    settings.MDB_NAME,
    "clusters",
    settings.MDB_USERNAME,
    settings.MDB_PASSWORD,
)
