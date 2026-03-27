"""Tests for app.h_terminal — Handle class (websocket terminal handler)."""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from plugins.manx.app.h_terminal import Handle


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestHandleInit:
    def test_tag_stored(self):
        h = Handle(tag='manx')
        assert h.tag == 'manx'

    def test_tag_empty_string(self):
        h = Handle(tag='')
        assert h.tag == ''

    def test_tag_custom_value(self):
        h = Handle(tag='custom-tag-123')
        assert h.tag == 'custom-tag-123'

    def test_tag_none(self):
        h = Handle(tag=None)
        assert h.tag is None


# ---------------------------------------------------------------------------
# run() — the static websocket handler
# ---------------------------------------------------------------------------

class TestHandleRun:

    @pytest.fixture
    def mock_socket(self):
        sock = AsyncMock()
        sock.recv = AsyncMock(return_value='whoami')
        sock.send = AsyncMock()
        return sock

    @pytest.fixture
    def handler_services(self, tcp_handler, fake_sessions):
        tcp_handler.sessions = list(fake_sessions)
        svc = {
            'term_svc': MagicMock(),
            'contact_svc': MagicMock(),
        }
        svc['term_svc'].socket_conn.tcp_handler = tcp_handler
        svc['contact_svc'].report = {'websocket': []}
        return svc

    @pytest.mark.asyncio
    async def test_run_sends_response(self, mock_socket, handler_services):
        """run() should recv a command, send it to tcp_handler, and send JSON back."""
        path = '/manx/1/ws'
        await Handle.run(mock_socket, path, handler_services)

        mock_socket.recv.assert_awaited_once()
        handler_services['term_svc'].socket_conn.tcp_handler.send.assert_awaited_once_with('1', 'whoami')
        mock_socket.send.assert_awaited_once()
        sent = json.loads(mock_socket.send.call_args[0][0])
        assert sent['response'] == 'output'
        assert sent['pwd'] == '/home'
        assert sent['status'] == 0
        assert sent['response_time'] == '50ms'

    @pytest.mark.asyncio
    async def test_run_appends_to_report(self, mock_socket, handler_services):
        """run() should append an entry to the websocket report."""
        path = '/manx/1/ws'
        await Handle.run(mock_socket, path, handler_services)

        report = handler_services['contact_svc'].report['websocket']
        assert len(report) == 1
        assert report[0]['paw'] == 'abc123'
        assert report[0]['cmd'] == 'whoami'
        assert 'date' in report[0]

    @pytest.mark.asyncio
    async def test_run_with_second_session(self, mock_socket, handler_services):
        """run() should correctly resolve paw for session id 2."""
        path = '/manx/2/ws'
        await Handle.run(mock_socket, path, handler_services)

        report = handler_services['contact_svc'].report['websocket']
        assert report[0]['paw'] == 'def456'

    @pytest.mark.asyncio
    async def test_run_strips_response_whitespace(self, mock_socket, handler_services):
        """run() should strip whitespace from the response."""
        handler_services['term_svc'].socket_conn.tcp_handler.send = AsyncMock(
            return_value=(0, '/tmp', '  padded output  ', '10ms')
        )
        path = '/manx/1/ws'
        await Handle.run(mock_socket, path, handler_services)

        sent = json.loads(mock_socket.send.call_args[0][0])
        assert sent['response'] == 'padded output'

    @pytest.mark.asyncio
    async def test_run_empty_command(self, mock_socket, handler_services):
        """run() should handle an empty command string."""
        mock_socket.recv = AsyncMock(return_value='')
        path = '/manx/1/ws'
        await Handle.run(mock_socket, path, handler_services)

        handler_services['term_svc'].socket_conn.tcp_handler.send.assert_awaited_once_with('1', '')

    @pytest.mark.asyncio
    async def test_run_nonzero_status(self, mock_socket, handler_services):
        """run() should forward non-zero status codes."""
        handler_services['term_svc'].socket_conn.tcp_handler.send = AsyncMock(
            return_value=(1, '/root', 'permission denied', '5ms')
        )
        path = '/manx/1/ws'
        await Handle.run(mock_socket, path, handler_services)

        sent = json.loads(mock_socket.send.call_args[0][0])
        assert sent['status'] == 1
        assert sent['response'] == 'permission denied'

    @pytest.mark.asyncio
    async def test_run_session_not_found_raises(self, mock_socket, handler_services):
        """run() should raise RuntimeError (wrapping StopIteration) when session id doesn't exist."""
        path = '/manx/999/ws'
        with pytest.raises(RuntimeError):
            await Handle.run(mock_socket, path, handler_services)

    @pytest.mark.asyncio
    async def test_run_multipart_path(self, mock_socket, handler_services):
        """run() extracts session_id from path.split('/')[2] regardless of extra segments."""
        path = '/manx/1/ws/extra/stuff'
        await Handle.run(mock_socket, path, handler_services)

        handler_services['term_svc'].socket_conn.tcp_handler.send.assert_awaited_once_with('1', 'whoami')

    @pytest.mark.asyncio
    async def test_run_date_format(self, mock_socket, handler_services):
        """The date written to the report should follow TIME_FORMAT."""
        path = '/manx/1/ws'
        await Handle.run(mock_socket, path, handler_services)

        report = handler_services['contact_svc'].report['websocket']
        date_str = report[0]['date']
        # Should be parseable as UTC time in the expected format
        parsed = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
        assert parsed is not None

    @pytest.mark.asyncio
    async def test_run_response_is_valid_json(self, mock_socket, handler_services):
        """The data sent back over the socket should be valid JSON."""
        path = '/manx/1/ws'
        await Handle.run(mock_socket, path, handler_services)

        raw = mock_socket.send.call_args[0][0]
        data = json.loads(raw)
        assert set(data.keys()) == {'response', 'pwd', 'status', 'response_time'}

    @pytest.mark.asyncio
    async def test_run_special_characters_in_command(self, mock_socket, handler_services):
        """run() should handle commands with special characters."""
        mock_socket.recv = AsyncMock(return_value='echo "hello; rm -rf /" | cat')
        path = '/manx/1/ws'
        await Handle.run(mock_socket, path, handler_services)

        report = handler_services['contact_svc'].report['websocket']
        assert report[0]['cmd'] == 'echo "hello; rm -rf /" | cat'

    @pytest.mark.asyncio
    async def test_run_unicode_command(self, mock_socket, handler_services):
        """run() should handle unicode commands."""
        mock_socket.recv = AsyncMock(return_value='echo "\u00e9\u00e8\u00ea"')
        path = '/manx/1/ws'
        await Handle.run(mock_socket, path, handler_services)

        report = handler_services['contact_svc'].report['websocket']
        assert '\u00e9' in report[0]['cmd']
