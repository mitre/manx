"""Tests for app.term_api — TermApi class (HTTP endpoint handlers)."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from plugins.manx.app.term_api import TermApi
from tests.conftest import FakeAbility, FakeAgent, FakeSession


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestTermApiInit:
    def test_services_assigned(self, mock_services):
        api = TermApi(mock_services)
        assert api.auth_svc is mock_services['auth_svc']
        assert api.file_svc is mock_services['file_svc']
        assert api.data_svc is mock_services['data_svc']
        assert api.contact_svc is mock_services['contact_svc']
        assert api.app_svc is mock_services['app_svc']
        assert api.rest_svc is mock_services['rest_svc']

    def test_term_svc_created(self, mock_services):
        api = TermApi(mock_services)
        assert api.term_svc is not None


# ---------------------------------------------------------------------------
# splash()
# ---------------------------------------------------------------------------

class TestSplash:

    @pytest.fixture
    def api(self, mock_services):
        return TermApi(mock_services)

    @pytest.mark.asyncio
    async def test_splash_returns_sessions_and_websocket(self, api, mock_request):
        result = await api.splash(mock_request())
        assert 'sessions' in result
        assert 'websocket' in result

    @pytest.mark.asyncio
    async def test_splash_session_fields(self, api, mock_request):
        result = await api.splash(mock_request())
        for s in result['sessions']:
            assert 'id' in s
            assert 'info' in s
            assert 'platform' in s
            assert 'executors' in s

    @pytest.mark.asyncio
    async def test_splash_calls_refresh(self, api, mock_request):
        await api.splash(mock_request())
        api.term_svc.socket_conn.tcp_handler.refresh.assert_awaited()

    @pytest.mark.asyncio
    async def test_splash_no_sessions(self, mock_services, mock_request):
        mock_services['contact_svc'].contacts[0].tcp_handler.sessions = []
        api = TermApi(mock_services)
        result = await api.splash(mock_request())
        assert result['sessions'] == []

    @pytest.mark.asyncio
    async def test_splash_handles_exception(self, mock_services, mock_request, capsys):
        """splash() catches exceptions and prints them."""
        mock_services['data_svc'].locate = AsyncMock(side_effect=RuntimeError('boom'))
        api = TermApi(mock_services)
        result = await api.splash(mock_request())
        captured = capsys.readouterr()
        assert 'boom' in captured.out
        assert result is None

    @pytest.mark.asyncio
    async def test_splash_multiple_sessions(self, api, mock_request):
        result = await api.splash(mock_request())
        assert len(result['sessions']) == 2

    @pytest.mark.asyncio
    async def test_splash_websocket_config(self, api, mock_request):
        result = await api.splash(mock_request())
        assert result['websocket'] == 'ws://localhost:7012'


# ---------------------------------------------------------------------------
# get_sessions()
# ---------------------------------------------------------------------------

class TestGetSessions:

    @pytest.fixture
    def api(self, mock_services):
        return TermApi(mock_services)

    @pytest.mark.asyncio
    async def test_returns_json_response(self, api, mock_request):
        resp = await api.get_sessions(mock_request())
        data = resp.data
        assert 'sessions' in data

    @pytest.mark.asyncio
    async def test_session_count(self, api, mock_request):
        resp = await api.get_sessions(mock_request())
        assert len(resp.data['sessions']) == 2

    @pytest.mark.asyncio
    async def test_session_structure(self, api, mock_request):
        resp = await api.get_sessions(mock_request())
        for s in resp.data['sessions']:
            assert set(s.keys()) == {'id', 'info', 'platform', 'executors'}

    @pytest.mark.asyncio
    async def test_calls_refresh(self, api, mock_request):
        await api.get_sessions(mock_request())
        api.term_svc.socket_conn.tcp_handler.refresh.assert_awaited()

    @pytest.mark.asyncio
    async def test_empty_sessions(self, mock_services, mock_request):
        mock_services['contact_svc'].contacts[0].tcp_handler.sessions = []
        api = TermApi(mock_services)
        resp = await api.get_sessions(mock_request())
        assert resp.data['sessions'] == []

    @pytest.mark.asyncio
    async def test_agent_not_found_for_session(self, mock_services, mock_request):
        """If data_svc.locate returns nothing for a paw, the session is not included."""
        mock_services['data_svc'].locate = AsyncMock(return_value=[])
        api = TermApi(mock_services)
        resp = await api.get_sessions(mock_request())
        assert resp.data['sessions'] == []


# ---------------------------------------------------------------------------
# sessions() (POST)
# ---------------------------------------------------------------------------

class TestSessionsPost:

    @pytest.fixture
    def api(self, mock_services):
        return TermApi(mock_services)

    @pytest.mark.asyncio
    async def test_returns_list(self, api, mock_request):
        resp = await api.sessions(mock_request())
        assert isinstance(resp.data, list)

    @pytest.mark.asyncio
    async def test_session_fields(self, api, mock_request):
        resp = await api.sessions(mock_request())
        for s in resp.data:
            assert 'id' in s
            assert 'info' in s
            assert set(s.keys()) == {'id', 'info'}

    @pytest.mark.asyncio
    async def test_session_count_matches(self, api, mock_request):
        resp = await api.sessions(mock_request())
        assert len(resp.data) == 2

    @pytest.mark.asyncio
    async def test_calls_refresh(self, api, mock_request):
        await api.sessions(mock_request())
        api.term_svc.socket_conn.tcp_handler.refresh.assert_awaited()

    @pytest.mark.asyncio
    async def test_empty_sessions(self, mock_services, mock_request):
        mock_services['contact_svc'].contacts[0].tcp_handler.sessions = []
        api = TermApi(mock_services)
        resp = await api.sessions(mock_request())
        assert resp.data == []

    @pytest.mark.asyncio
    async def test_info_is_paw(self, api, mock_request):
        resp = await api.sessions(mock_request())
        paws = [s['info'] for s in resp.data]
        assert 'abc123' in paws
        assert 'def456' in paws


# ---------------------------------------------------------------------------
# get_history()
# ---------------------------------------------------------------------------

class TestGetHistory:

    @pytest.fixture
    def api(self, mock_services):
        mock_services['contact_svc'].report = {
            'websocket': [
                {'paw': 'abc123', 'cmd': 'ls', 'date': '2025-01-01T00:00:00Z'},
                {'paw': 'abc123', 'cmd': 'pwd', 'date': '2025-01-01T00:01:00Z'},
                {'paw': 'other', 'cmd': 'whoami', 'date': '2025-01-01T00:02:00Z'},
            ]
        }
        return TermApi(mock_services)

    @pytest.mark.asyncio
    async def test_returns_matching_history(self, api, mock_request):
        req = mock_request(json_data={'paw': 'abc123'})
        resp = await api.get_history(req)
        assert len(resp.data) == 2

    @pytest.mark.asyncio
    async def test_filters_by_paw(self, api, mock_request):
        req = mock_request(json_data={'paw': 'other'})
        resp = await api.get_history(req)
        assert len(resp.data) == 1
        assert resp.data[0]['cmd'] == 'whoami'

    @pytest.mark.asyncio
    async def test_no_matching_paw(self, api, mock_request):
        req = mock_request(json_data={'paw': 'nonexistent'})
        resp = await api.get_history(req)
        assert resp.data == []

    @pytest.mark.asyncio
    async def test_empty_report(self, mock_services, mock_request):
        mock_services['contact_svc'].report = {'websocket': []}
        api = TermApi(mock_services)
        req = mock_request(json_data={'paw': 'abc123'})
        resp = await api.get_history(req)
        assert resp.data == []

    @pytest.mark.asyncio
    async def test_missing_paw_in_request(self, api, mock_request):
        """If paw is missing from request, data.get('paw') returns None, no match."""
        req = mock_request(json_data={})
        resp = await api.get_history(req)
        assert resp.data == []

    @pytest.mark.asyncio
    async def test_history_preserves_entry_structure(self, api, mock_request):
        req = mock_request(json_data={'paw': 'abc123'})
        resp = await api.get_history(req)
        for entry in resp.data:
            assert 'paw' in entry
            assert 'cmd' in entry
            assert 'date' in entry


# ---------------------------------------------------------------------------
# get_abilities()
# ---------------------------------------------------------------------------

class TestGetAbilities:

    @pytest.fixture
    def api(self, mock_services):
        abilities = [FakeAbility('a1', 'recon'), FakeAbility('a2', 'exfil')]
        mock_services['rest_svc'].find_abilities = AsyncMock(return_value=abilities)
        return TermApi(mock_services)

    @pytest.mark.asyncio
    async def test_returns_abilities(self, api, mock_request):
        req = mock_request(json_data={'paw': 'abc123'})
        resp = await api.get_abilities(req)
        assert 'abilities' in resp.data
        assert len(resp.data['abilities']) == 2

    @pytest.mark.asyncio
    async def test_ability_display_format(self, api, mock_request):
        req = mock_request(json_data={'paw': 'abc123'})
        resp = await api.get_abilities(req)
        for a in resp.data['abilities']:
            assert 'ability_id' in a
            assert 'name' in a

    @pytest.mark.asyncio
    async def test_no_abilities(self, mock_services, mock_request):
        mock_services['rest_svc'].find_abilities = AsyncMock(return_value=[])
        api = TermApi(mock_services)
        req = mock_request(json_data={'paw': 'abc123'})
        resp = await api.get_abilities(req)
        assert resp.data['abilities'] == []

    @pytest.mark.asyncio
    async def test_calls_rest_svc_with_paw(self, api, mock_request):
        req = mock_request(json_data={'paw': 'test-paw'})
        await api.get_abilities(req)
        api.rest_svc.find_abilities.assert_awaited_once_with(paw='test-paw')

    @pytest.mark.asyncio
    async def test_missing_paw_raises(self, api, mock_request):
        """If 'paw' key is absent, KeyError should be raised."""
        req = mock_request(json_data={})
        with pytest.raises(KeyError):
            await api.get_abilities(req)


# ---------------------------------------------------------------------------
# dynamically_compile()
# ---------------------------------------------------------------------------

class TestDynamicallyCompile:

    @pytest.fixture
    def api(self, mock_services):
        return TermApi(mock_services)

    @pytest.mark.asyncio
    @patch('plugins.manx.app.term_api.which', return_value='/usr/local/go/bin/go')
    async def test_compile_with_go_available(self, mock_which, api):
        headers = {'file': 'manx.go', 'platform': 'linux'}
        result = await api.dynamically_compile(headers)
        api.file_svc.find_file_path.assert_awaited_once_with('manx.go')
        api.file_svc.compile_go.assert_awaited_once()
        assert result == b'compiled_binary'

    @pytest.mark.asyncio
    @patch('plugins.manx.app.term_api.which', return_value=None)
    async def test_compile_without_go(self, mock_which, api):
        """When go is not installed, skip compilation but still retrieve."""
        headers = {'file': 'manx.go', 'platform': 'linux'}
        result = await api.dynamically_compile(headers)
        api.file_svc.compile_go.assert_not_awaited()
        api.app_svc.retrieve_compiled_file.assert_awaited_once_with('manx.go', 'linux')

    @pytest.mark.asyncio
    @patch('plugins.manx.app.term_api.which', return_value='/usr/local/go/bin/go')
    async def test_compile_with_contact_header(self, mock_which, api):
        headers = {'file': 'manx.go', 'platform': 'windows', 'contact': 'tcp'}
        await api.dynamically_compile(headers)
        call_kwargs = api.file_svc.compile_go.call_args
        ldflags = call_kwargs.kwargs.get('ldflags', '') or call_kwargs[1].get('ldflags', '')
        assert 'main.contact=tcp' in ldflags

    @pytest.mark.asyncio
    @patch('plugins.manx.app.term_api.which', return_value='/usr/local/go/bin/go')
    async def test_compile_with_socket_header(self, mock_which, api):
        headers = {'file': 'manx.go', 'platform': 'linux', 'socket': '0.0.0.0:7010'}
        await api.dynamically_compile(headers)
        call_kwargs = api.file_svc.compile_go.call_args
        ldflags = call_kwargs.kwargs.get('ldflags', '') or call_kwargs[1].get('ldflags', '')
        assert 'main.socket=0.0.0.0:7010' in ldflags

    @pytest.mark.asyncio
    @patch('plugins.manx.app.term_api.which', return_value='/usr/local/go/bin/go')
    async def test_compile_with_http_header(self, mock_which, api):
        headers = {'file': 'manx.go', 'platform': 'darwin', 'http': 'http://localhost:8888'}
        await api.dynamically_compile(headers)
        call_kwargs = api.file_svc.compile_go.call_args
        ldflags = call_kwargs.kwargs.get('ldflags', '') or call_kwargs[1].get('ldflags', '')
        assert 'main.http=http://localhost:8888' in ldflags

    @pytest.mark.asyncio
    @patch('plugins.manx.app.term_api.which', return_value='/usr/local/go/bin/go')
    async def test_compile_all_optional_headers(self, mock_which, api):
        headers = {
            'file': 'manx.go',
            'platform': 'linux',
            'contact': 'tcp',
            'socket': '0.0.0.0:7010',
            'http': 'http://localhost:8888',
        }
        await api.dynamically_compile(headers)
        call_kwargs = api.file_svc.compile_go.call_args
        ldflags = call_kwargs.kwargs.get('ldflags', '') or call_kwargs[1].get('ldflags', '')
        assert 'main.contact=tcp' in ldflags
        assert 'main.socket=0.0.0.0:7010' in ldflags
        assert 'main.http=http://localhost:8888' in ldflags

    @pytest.mark.asyncio
    @patch('plugins.manx.app.term_api.which', return_value='/usr/local/go/bin/go')
    async def test_compile_default_architecture(self, mock_which, api):
        headers = {'file': 'manx.go', 'platform': 'linux'}
        await api.dynamically_compile(headers)
        call_kwargs = api.file_svc.compile_go.call_args
        assert call_kwargs.kwargs.get('arch', '') == 'amd64' or call_kwargs[1].get('arch', '') == 'amd64'

    @pytest.mark.asyncio
    @patch('plugins.manx.app.term_api.which', return_value='/usr/local/go/bin/go')
    async def test_compile_custom_architecture(self, mock_which, api):
        headers = {'file': 'manx.go', 'platform': 'linux', 'architecture': 'arm64'}
        await api.dynamically_compile(headers)
        call_kwargs = api.file_svc.compile_go.call_args
        assert call_kwargs.kwargs.get('arch', '') == 'arm64' or call_kwargs[1].get('arch', '') == 'arm64'

    @pytest.mark.asyncio
    @patch('plugins.manx.app.term_api.which', return_value='/usr/local/go/bin/go')
    async def test_compile_ldflags_contain_key(self, mock_which, api):
        """ldflags should always include -s -w and a generated key."""
        headers = {'file': 'manx.go', 'platform': 'linux'}
        await api.dynamically_compile(headers)
        call_kwargs = api.file_svc.compile_go.call_args
        ldflags = call_kwargs.kwargs.get('ldflags', '') or call_kwargs[1].get('ldflags', '')
        assert '-s' in ldflags
        assert '-w' in ldflags
        assert 'main.key=' in ldflags

    @pytest.mark.asyncio
    @patch('plugins.manx.app.term_api.which', return_value='/usr/local/go/bin/go')
    async def test_compile_output_path(self, mock_which, api):
        headers = {'file': 'manx.go', 'platform': 'linux'}
        await api.dynamically_compile(headers)
        call_kwargs = api.file_svc.compile_go.call_args
        output = call_kwargs[0][1] if len(call_kwargs[0]) > 1 else call_kwargs.kwargs.get('output', '')
        # output is the second positional arg to compile_go(platform, output, ...)
        assert 'manx.go-linux' in str(output)

    @pytest.mark.asyncio
    @patch('plugins.manx.app.term_api.which', return_value='/usr/local/go/bin/go')
    async def test_compile_sanitizes_ldflag_values(self, mock_which, api):
        """file_svc.sanitize_ldflag_value should be called for each param header."""
        headers = {'file': 'manx.go', 'platform': 'linux', 'contact': 'tcp', 'socket': '0.0.0.0:7010'}
        await api.dynamically_compile(headers)
        assert api.file_svc.sanitize_ldflag_value.call_count == 2

    @pytest.mark.asyncio
    @patch('plugins.manx.app.term_api.which', return_value='/usr/local/go/bin/go')
    async def test_compile_returns_binary(self, mock_which, api):
        headers = {'file': 'manx.go', 'platform': 'windows'}
        result = await api.dynamically_compile(headers)
        assert result == b'compiled_binary'
