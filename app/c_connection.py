"""Async connection wrapper for TCP sessions.

Wraps asyncio StreamReader/StreamWriter to provide a simple async
send/recv interface, replacing the deprecated use of raw sockets
obtained via writer.get_extra_info('socket') which returns a
TransportSocket that lacks send()/recv() methods.

See: https://github.com/mitre/manx/issues/51
"""

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
