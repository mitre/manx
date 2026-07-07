import asyncio
import unittest


class TestConnection(unittest.TestCase):
    """Tests for the Connection class that wraps asyncio streams."""

    def test_connection_init(self):
        """Connection stores reader and writer references."""
        from app.c_connection import Connection

        mock_reader = object()
        mock_writer = object()
        conn = Connection(mock_reader, mock_writer)
        self.assertIs(conn.reader, mock_reader)
        self.assertIs(conn.writer, mock_writer)

    def test_recv(self):
        """Connection.recv reads from the underlying StreamReader."""
        from app.c_connection import Connection

        class MockReader:
            def __init__(self):
                self.read_called_with = None

            async def read(self, n):
                self.read_called_with = n
                return b"hello"

        class MockWriter:
            pass

        reader = MockReader()
        conn = Connection(reader, MockWriter())
        result = asyncio.get_event_loop().run_until_complete(conn.recv(1024))
        self.assertEqual(result, b"hello")
        self.assertEqual(reader.read_called_with, 1024)

    def test_send_bytes(self):
        """Connection.send writes bytes to the underlying StreamWriter."""
        from app.c_connection import Connection

        class MockReader:
            pass

        class MockWriter:
            def __init__(self):
                self.written = None
                self.drained = False

            def write(self, data):
                self.written = data

            async def drain(self):
                self.drained = True

        writer = MockWriter()
        conn = Connection(MockReader(), writer)
        asyncio.get_event_loop().run_until_complete(conn.send(b"world"))
        self.assertEqual(writer.written, b"world")
        self.assertTrue(writer.drained)

    def test_send_str_encodes_to_bytes(self):
        """Connection.send encodes str to bytes before writing."""
        from app.c_connection import Connection

        class MockReader:
            pass

        class MockWriter:
            def __init__(self):
                self.written = None

            def write(self, data):
                self.written = data

            async def drain(self):
                pass

        writer = MockWriter()
        conn = Connection(MockReader(), writer)
        asyncio.get_event_loop().run_until_complete(conn.send("text"))
        self.assertEqual(writer.written, b"text")

    def test_close(self):
        """Connection.close closes the underlying writer."""
        from app.c_connection import Connection

        class MockReader:
            pass

        class MockWriter:
            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

        writer = MockWriter()
        conn = Connection(MockReader(), writer)
        conn.close()
        self.assertTrue(writer.closed)


class TestHandleWebSocket(unittest.TestCase):
    """Tests for the updated WebSocket API usage in h_terminal.py Handle."""

    def test_handle_uses_receive_and_send_str(self):
        """Verify Handle.run uses socket.receive() and socket.send_str()."""
        import ast
        with open("app/h_terminal.py") as f:
            source = f.read()

        # Ensure deprecated methods are not used
        self.assertNotIn("socket.recv()", source,
                         "Should use socket.receive() instead of deprecated socket.recv()")
        self.assertNotIn("await socket.send(", source,
                         "Should use socket.send_str() instead of deprecated socket.send()")

        # Ensure modern methods are used
        self.assertIn("socket.receive()", source,
                      "Should call socket.receive() for reading WebSocket messages")
        self.assertIn("socket.send_str(", source,
                      "Should call socket.send_str() for sending WebSocket messages")


if __name__ == "__main__":
    unittest.main()
