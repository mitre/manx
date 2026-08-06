"""Tests for the Connection wrapper class."""

import asyncio
from unittest import mock

import pytest

from plugins.manx.app.c_connection import Connection


@pytest.fixture
def mock_reader():
    reader = mock.AsyncMock()
    return reader


@pytest.fixture
def mock_writer():
    writer = mock.Mock()
    writer.write = mock.Mock()
    writer.drain = mock.AsyncMock()
    return writer


@pytest.fixture
def connection(mock_reader, mock_writer):
    return Connection(mock_reader, mock_writer)


class TestConnection:

    @pytest.mark.asyncio
    async def test_recv_delegates_to_reader(self, connection, mock_reader):
        mock_reader.read.return_value = b'hello'
        result = await connection.recv(1024)
        assert result == b'hello'
        mock_reader.read.assert_awaited_once_with(1024)

    @pytest.mark.asyncio
    async def test_send_writes_and_drains(self, connection, mock_writer):
        await connection.send(b'world')
        mock_writer.write.assert_called_once_with(b'world')
        mock_writer.drain.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_empty_data(self, connection, mock_writer):
        await connection.send(b'')
        mock_writer.write.assert_called_once_with(b'')
        mock_writer.drain.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_recv_empty(self, connection, mock_reader):
        mock_reader.read.return_value = b''
        result = await connection.recv(4096)
        assert result == b''
