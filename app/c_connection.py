class Connection:
    """Wraps asyncio StreamReader/StreamWriter to provide send/recv interface.

    Python 3.12 removed the deprecated asyncio.Transport send/recv methods.
    This class provides a compatible interface using the modern
    StreamReader/StreamWriter API.
    """

    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    async def recv(self, num_bytes):
        """Read up to num_bytes from the stream."""
        return await self.reader.read(num_bytes)

    async def send(self, data):
        """Write data to the stream and flush."""
        if isinstance(data, str):
            data = data.encode()
        self.writer.write(data)
        await self.writer.drain()

    def close(self):
        """Close the underlying writer."""
        self.writer.close()
