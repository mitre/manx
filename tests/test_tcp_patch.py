"""Tests for the TCP handler patch."""

import json
import socket
from unittest import mock

import pytest

from plugins.manx.app.c_connection import Connection
from plugins.manx.app.c_session import Session
from plugins.manx.app.tcp_patch import (
    patch_tcp_handler,
    _patched_accept,
    _patched_refresh,
    _patched_send,
)


def _make_handler(sessions=None):
    """Create a mock TcpSessionHandler."""
    handler = mock.Mock()
    handler.sessions = sessions or []
    handler.log = mock.Mock()
    handler.services = mock.Mock()
    handler.generate_number = mock.Mock(return_value=123456)
    return handler


class TestPatchedRefresh:

    @pytest.mark.asyncio
    async def test_removes_dead_sessions(self):
        handler = _make_handler()

        dead_conn = mock.AsyncMock()
        dead_conn.send.side_effect = OSError('connection reset')
        dead_session = mock.Mock()
        dead_session.connection = dead_conn
        dead_session.id = 1

        live_conn = mock.AsyncMock()
        live_session = mock.Mock()
        live_session.connection = live_conn
        live_session.id = 2

        handler.sessions = [dead_session, live_session]
        await _patched_refresh(handler)

        assert len(handler.sessions) == 1
        assert handler.sessions[0].id == 2

    @pytest.mark.asyncio
    async def test_keeps_all_live_sessions(self):
        handler = _make_handler()

        sessions = []
        for i in range(3):
            conn = mock.AsyncMock()
            s = mock.Mock()
            s.connection = conn
            s.id = i
            sessions.append(s)

        handler.sessions = sessions
        await _patched_refresh(handler)
        assert len(handler.sessions) == 3

    @pytest.mark.asyncio
    async def test_removes_all_dead_sessions(self):
        handler = _make_handler()

        sessions = []
        for i in range(3):
            conn = mock.AsyncMock()
            conn.send.side_effect = ConnectionError()
            s = mock.Mock()
            s.connection = conn
            s.id = i
            sessions.append(s)

        handler.sessions = sessions
        await _patched_refresh(handler)
        assert len(handler.sessions) == 0


class TestPatchedSend:

    @pytest.mark.asyncio
    async def test_send_returns_parsed_response(self):
        handler = _make_handler()
        conn = mock.AsyncMock()
        session = Session(id=42, paw='testpaw', connection=conn)
        handler.sessions = [session]

        response_data = {
            'status': 0,
            'pwd': '/home/test',
            'response': 'root',
            'agent_reported_time': '2024-01-01T00:00:00Z'
        }

        # Mock _attempt_connection on the handler
        async def mock_attempt(self_unused, sid, c, timeout):
            return json.dumps(response_data)

        import plugins.manx.app.tcp_patch as tcp_patch_mod
        original = tcp_patch_mod._patched_attempt_connection
        tcp_patch_mod._patched_attempt_connection = mock_attempt
        try:
            status, pwd, response, ts = await _patched_send(handler, 42, 'whoami')
            assert status == 0
            assert pwd == '/home/test'
            assert response == 'root'
            assert ts == '2024-01-01T00:00:00Z'
        finally:
            tcp_patch_mod._patched_attempt_connection = original

    @pytest.mark.asyncio
    async def test_send_handles_exception(self):
        handler = _make_handler()
        conn = mock.AsyncMock()
        conn.send.side_effect = Exception('broken')
        session = Session(id=42, paw='testpaw', connection=conn)
        handler.sessions = [session]

        status, pwd, response, ts = await _patched_send(handler, 42, 'whoami')
        assert status == 1
        assert pwd == '~$ '
        assert 'broken' in response


class TestPatchTcpHandler:

    def test_patches_handler_with_old_api(self):
        """Test that patch_tcp_handler replaces methods on a handler
        whose accept method references get_extra_info."""
        handler = _make_handler()

        # Create a fake accept method that contains 'get_extra_info'
        async def old_accept(reader, writer):
            connection = writer.get_extra_info('socket')

        handler.accept = old_accept
        handler.refresh = mock.AsyncMock()
        handler.send = mock.AsyncMock()
        handler._attempt_connection = mock.AsyncMock()

        patch_tcp_handler(handler)

        # After patching, the methods should be bound methods of the patched functions
        assert 'patched' in handler.accept.__func__.__name__

    def test_skips_handler_without_old_api(self):
        """Test that patch_tcp_handler is a no-op when handler already uses modern API."""
        handler = _make_handler()

        async def modern_accept(reader, writer):
            # No get_extra_info here
            pass

        handler.accept = modern_accept
        original_accept = handler.accept

        patch_tcp_handler(handler)

        # Should not have been replaced
        assert handler.accept is original_accept
