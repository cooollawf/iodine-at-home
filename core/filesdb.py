import atexit
import asyncio
import aiosqlite
from aiosqlite import Cursor
from pathlib import Path


class FilesDB:
    def __init__(self):
        self.conn = None

    # def __init__(self, ):
    #     self.client = motor.motor_asyncio.AsyncIOMotorClient(f"mongodb://{settings.MDB_USERNAME}:{settings.MDB_PASSWORD}@{settings.MDB_HOST}")

    async def connect(self):
        self.conn = await aiosqlite.connect("./data/database.db")
        self.cursor = await self.conn.cursor()

    async def close(self):
        await self.conn.close()
        self.conn = None
        self.cursor = None

    async def create_table(self):
        await self.connect()
        await self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS FILELIST
            (
                HASH TEXT PRIMARY KEY,
                PATH TEXT,
                URL TEXT,
                SIZE INTEGER,
                MTIME INTEGER,
                SOURCE TEXT
            )
        """
        )
        await self.conn.commit()
        await self.close()
        

    async def new_file(
        self,
        hash: str,
        path: str = "",
        url: str = "",
        size: int = 0,
        mtime: int = 0,
        source: str = "local",
    ):
        await self.connect()
        await self.conn.execute(
            """
            INSERT INTO FILELIST (
                HASH,
                PATH,
                URL,
                SIZE,
                MTIME,
                SOURCE
            ) VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                hash,
                path,
                url,
                size,
                mtime,
                source,
            ),
        )
        await self.conn.commit()
        await self.close()
        return True

    async def delete_file(self, hash: str):
        await self.connect()
        await self.conn.execute(
            """
            DELETE FROM FILELIST WHERE HASH = ?
        """,
            (hash),
        )
        await self.conn.commit()
        await self.close()
        return True

    async def delete_all(self):
        await self.connect()
        await self.conn.execute(
            """
            DELETE FROM FILELIST
        """,
        )
        await self.conn.commit()
        await self.close()
        return True

    async def find_one(self, hash: str):
        await self.connect()
        async with self.conn.execute(
            """
            SELECT * FROM FILELIST WHERE HASH = ?
        """,
            (hash,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                result = dict(zip(columns, row))
            else:
                result = False
        await self.close()
        return result

    async def get_all(self):
        await self.connect()
        async with self.conn.execute("SELECT * FROM FILELIST") as cursor:
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            result = [dict(zip(columns, row)) for row in rows]
        await self.close()
        return result


filesdb = FilesDB()
asyncio.run(filesdb.create_table())