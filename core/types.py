import io
import os
import core.utils as utils
from typing import Optional
import core.database as database

class Cluster:
    def __init__(self, id: str):
        if database.query_cluster_data(id).any().any():
            self.id = id
            self.update()
        else:
            return False
    
    def update(self):
        self.secret = str(database.query_cluster_data(self.id)["CLUSTER_SECRET"].item())
        self.name = str(database.query_cluster_data(self.id)["CLUSTER_NAME"].item())
        self.trust = int(database.query_cluster_data(self.id)["CLUSTER_TRUST"].item())
        self.isBanned = int(database.query_cluster_data(self.id)["CLUSTER_ISBANNED"].item())
        self.ban_reason = str(database.query_cluster_data(self.id)["CLUSTER_BANREASON"].item())
        self.host = str(database.query_cluster_data(self.id)["CLUSTER_HOST"].item())
        self.port = int(database.query_cluster_data(self.id)["CLUSTER_PORT"].item())
        self.version = str(database.query_cluster_data(self.id)["CLUSTER_VERSION"].item())
        self.runtime = str(database.query_cluster_data(self.id)["CLUSTER_RUNTIME"].item())

    def edit(self, name: str = None, secret: str = None, bandwidth: int = None, trust: int = None, isBanned: bool = None, ban_reason: str = None, host: str = None, port: int = None, version: str = None, runtime: str = None):
        database.edit_cluster(self.id, name=name, secret=secret, bandwidth=bandwidth, trust=trust, is_banned=isBanned, ban_reason=ban_reason, host=host, port=port, version=version, runtime=runtime)
        self.update()
class Avro:
    def __init__(self, initial_bytes: bytes = b"", encoding: str = "utf-8") -> None:
        self.io = io.BytesIO(initial_bytes)
        self.encoding = encoding

    def read(self, __size: int | None = None):
        return self.io.read(__size)

    def readIntegetr(self):
        value = self.read(4)
        return (value[0] << 24) + (value[1] << 16) + (value[2] << 8) + (value[3] << 0)

    def readBoolean(self):
        return bool(int.from_bytes(self.read(1), byteorder="big"))

    def readShort(self):
        value = self.read(2)
        if value[0] | value[1] < 0:
            raise EOFError()
        return (value[0] << 8) + (value[1] << 0)

    def readLong(self) -> int:
        value = list(self.read(8))
        value = (
            (value[0] << 56)
            + ((value[1] & 255) << 48)
            + ((value[2] & 255) << 40)
            + ((value[3] & 255) << 32)
            + ((value[4] & 255) << 24)
            + ((value[5] & 255) << 16)
            + ((value[6] & 255) << 8)
            + ((value[7] & 255) << 0)
        )
        return value - 2**64 if value > 2**63 - 1 else value

    def readVarInt(self) -> int:
        b = ord(self.read(1))
        n = b & 0x7F
        shift = 7
        while (b & 0x80) != 0:
            b = ord(self.read(1))
            n |= (b & 0x7F) << shift
            shift += 7
        return (n >> 1) ^ -(n & 1)

    def readString(
        self, maximun: Optional[int] = None, encoding: Optional[str] = None
    ) -> str:
        return self.read(
            self.readVarInt()
            if maximun is None
            else min(self.readVarInt(), max(maximun, 0))
        ).decode(encoding or self.encoding)

    def readBytes(self, length: int) -> bytes:
        return self.read(length)

    def write(self, value: bytes | int):
        if isinstance(value, bytes):
            self.io.write(value)
        else:
            self.io.write((value + 256 if value < 0 else value).to_bytes(1, "big"))  # type: ignore

    def writeBoolean(self, value: bool):
        self.write(value.to_bytes(1, "big"))

    def writeShort(self, data: int):
        self.write(((data >> 8) & 0xFF).to_bytes(1, "big"))
        self.write(((data >> 0) & 0xFF).to_bytes(1, "big"))

    def writeInteger(self, data: int):
        self.write(((data >> 24) & 0xFF).to_bytes(1, "big"))
        self.write(((data >> 16) & 0xFF).to_bytes(1, "big"))
        self.write(((data >> 8) & 0xFF).to_bytes(1, "big"))
        self.write((data & 0xFF).to_bytes(1, "big"))

    def writeVarInt(self, value: int):
        self.write(Avro.getVarInt(value))

    def writeString(self, data: str, encoding: Optional[str] = None):
        self.writeVarInt(len(data.encode(encoding or self.encoding)))
        self.write(data.encode(encoding or self.encoding))

    def writeLong(self, data: int):
        data = data - 2**64 if data > 2**63 - 1 else data
        self.write((data >> 56) & 0xFF)
        self.write((data >> 48) & 0xFF)
        self.write((data >> 40) & 0xFF)
        self.write((data >> 32) & 0xFF)
        self.write((data >> 24) & 0xFF)
        self.write((data >> 16) & 0xFF)
        self.write((data >> 8) & 0xFF)
        self.write((data >> 0) & 0xFF)

    def __sizeof__(self) -> int:
        return self.io.tell()

    def __len__(self) -> int:
        return self.io.tell()
    
    @staticmethod
    def getVarInt(data: int):
        r: bytes = b""
        data = (data << 1) ^ (data >> 63)
        while (data & ~0x7F) != 0:
            r += ((data & 0x7f) | 0x80).to_bytes(1, "big")
            data >>= 7
        r += data.to_bytes(1, "big")
        return r

class FileObject:
    def __init__(self, filepath: str):
        self.path = filepath.lstrip(".")
        self.hash = utils.hash_file(filepath)
        self.size = os.path.getsize(filepath)
        self.mtime = int(os.path.getmtime(filepath)*1000)