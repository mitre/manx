"""Patch for caldera's TcpSessionHandler to fix deprecated socket API.

Caldera 5.0.0's contact_tcp.py uses writer.get_extra_info('socket') which
returns a TransportSocket object that lacks send()/recv() methods, causing:

    AttributeError: 'TransportSocket' object has no attribute 'send'

This module patches the TCP handler at runtime to use asyncio
StreamReader/StreamWriter via the Connection wrapper instead.

If caldera has already been updated to use its own TCPSession class (main
branch), the patch detects this and is a no-op.

See: https://github.com/mitre/manx/issues/51
"""

import json
import socket
import time

from typing import Tuple

from plugins.manx.app.c_connection import Connection
from plugins.manx.app.c_session import Session


def _needs_patching(handler):
    """Check if the handler uses the old broken socket API.

    Returns False if the handler already uses modern stream-based sessions
    (e.g., caldera main branch with TCPSession).
    """
    # If the accept method references 'get_extra_info', it needs patching.
    # If it's already been patched or uses TCPSession, skip.
    import inspect
    try:
        source = inspect.getsource(handler.accept)
        return 'get_extra_info' in source
    except (OSError, TypeError):
        # Can't inspect, assume patching is safe (it's idempotent)
        return True


async def _patched_accept(self, reader, writer):
    """Replacement for TcpSessionHandler.accept that uses Connection wrapper."""
    try:
        profile = await self._handshake(reader)
    except Exception as e:
        self.log.debug('Handshake failed: %s' % e)
        return
    connection = Connection(reader, writer)
    profile['executors'] = [e for e in profile['executors'].split(',') if e]
    profile['contact'] = 'tcp'
    agent, _ = await self.services.get('contact_svc').handle_heartbeat(**profile)
    new_session = Session(id=self.generate_number(size=6), paw=agent.paw, connection=connection)
    self.sessions.append(new_session)
    await self.send(new_session.id, agent.paw, timeout=5)


async def _patched_refresh(self):
    """Replacement for TcpSessionHandler.refresh that uses async send."""
    index = 0
    while index < len(self.sessions):
        session = self.sessions[index]
        try:
            await session.connection.send(str.encode(' '))
        except (socket.error, OSError, ConnectionError):
            self.log.debug(
                'Error occurred when refreshing session %s. Removing from session pool.',
                session.id
            )
            del self.sessions[index]
        else:
            index += 1


async def _patched_send(self, session_id: int, cmd: str, timeout: int = 60) -> Tuple[int, str, str, str]:
    """Replacement for TcpSessionHandler.send that uses async Connection."""
    try:
        conn = next(i.connection for i in self.sessions if i.id == int(session_id))
        await conn.send(str.encode(' '))
        time.sleep(0.01)
        await conn.send(str.encode('%s\n' % cmd))
        response = await _patched_attempt_connection(self, session_id, conn, timeout=timeout)
        response = json.loads(response)
        return response['status'], response['pwd'], response['response'], response.get('agent_reported_time', '')
    except Exception as e:
        self.log.exception(e)
        return 1, '~$ ', str(e), ''


async def _patched_attempt_connection(self, session_id, connection, timeout):
    """Replacement for TcpSessionHandler._attempt_connection using async recv."""
    buffer = 4096
    data = b''
    waited_seconds = 0
    time.sleep(0.1)  # initial wait for fast operations.
    while True:
        try:
            part = await connection.recv(buffer)
            data += part
            if len(part) < buffer:
                break
        except BlockingIOError as err:
            if waited_seconds < timeout:
                time.sleep(1)
                waited_seconds += 1
            else:
                self.log.error("Timeout reached for session %s", session_id)
                return json.dumps(dict(status=1, pwd='~$ ', response=str(err)))
    return str(data, 'utf-8')


def patch_tcp_handler(handler):
    """Apply the modern async stream patches to a TcpSessionHandler instance.

    This is safe to call even if the handler has already been updated:
    it checks whether patching is needed first.
    """
    if not _needs_patching(handler):
        return

    import types
    handler.accept = types.MethodType(_patched_accept, handler)
    handler.refresh = types.MethodType(_patched_refresh, handler)
    handler.send = types.MethodType(_patched_send, handler)
    handler._attempt_connection = types.MethodType(_patched_attempt_connection, handler)
