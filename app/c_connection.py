from app.utility.base_object import BaseObject


class Connection(BaseObject):

    def __init__(self, reader, writer):
        super().__init__()
        self.reader = reader
        self.writer = writer

    async def recv(self, num_bytes):
        return await self.reader.read(num_bytes)

    async def send(self, data):
        self.writer.write(data)
        await self.writer.drain()
