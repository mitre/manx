"""Tests for hook.py — plugin entry point."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestHookModuleAttributes:

    def test_name(self):
        from plugins.manx import hook
        assert hook.name == 'Terminal'

    def test_description(self):
        from plugins.manx import hook
        assert hook.description == 'A toolset which supports terminal access'

    def test_address(self):
        from plugins.manx import hook
        assert hook.address == '/plugin/manx/gui'

    def test_access(self):
        from plugins.manx import hook
        assert hook.access == 'red'


class TestHookEnable:

    @pytest.fixture
    def services(self, mock_services):
        return mock_services

    @pytest.mark.asyncio
    async def test_enable_applies_sessions(self, services):
        from plugins.manx.hook import enable
        await enable(services)
        services['data_svc'].apply.assert_awaited_once_with('sessions')

    @pytest.mark.asyncio
    async def test_enable_adds_routes(self, services):
        from plugins.manx.hook import enable
        await enable(services)
        router = services['app_svc'].application.router
        # 5 add_route calls + 1 add_static
        assert router.add_route.call_count == 5
        assert router.add_static.call_count == 1

    @pytest.mark.asyncio
    async def test_enable_registers_static_route(self, services):
        from plugins.manx.hook import enable
        await enable(services)
        router = services['app_svc'].application.router
        router.add_static.assert_called_once_with('/manx', 'plugins/manx/static/', append_version=True)

    @pytest.mark.asyncio
    async def test_enable_registers_gui_route(self, services):
        from plugins.manx.hook import enable
        await enable(services)
        router = services['app_svc'].application.router
        calls = [c for c in router.add_route.call_args_list if c[0][1] == '/plugin/manx/gui']
        assert len(calls) == 1
        assert calls[0][0][0] == 'GET'

    @pytest.mark.asyncio
    async def test_enable_registers_get_sessions_route(self, services):
        from plugins.manx.hook import enable
        await enable(services)
        router = services['app_svc'].application.router
        calls = [c for c in router.add_route.call_args_list if c[0][1] == '/plugin/manx/sessions']
        # One GET and one POST
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_enable_registers_history_route(self, services):
        from plugins.manx.hook import enable
        await enable(services)
        router = services['app_svc'].application.router
        calls = [c for c in router.add_route.call_args_list if c[0][1] == '/plugin/manx/history']
        assert len(calls) == 1
        assert calls[0][0][0] == 'POST'

    @pytest.mark.asyncio
    async def test_enable_registers_ability_route(self, services):
        from plugins.manx.hook import enable
        await enable(services)
        router = services['app_svc'].application.router
        calls = [c for c in router.add_route.call_args_list if c[0][1] == '/plugin/manx/ability']
        assert len(calls) == 1
        assert calls[0][0][0] == 'POST'

    @pytest.mark.asyncio
    async def test_enable_appends_handle_to_websocket(self, services):
        from plugins.manx.hook import enable
        ws_contact = services['contact_svc'].contacts[1]
        initial_count = len(ws_contact.handler.handles)
        await enable(services)
        assert len(ws_contact.handler.handles) == initial_count + 1

    @pytest.mark.asyncio
    async def test_enable_handle_tag_is_manx(self, services):
        from plugins.manx.hook import enable
        ws_contact = services['contact_svc'].contacts[1]
        await enable(services)
        handle = ws_contact.handler.handles[-1]
        assert handle.tag == 'manx'

    @pytest.mark.asyncio
    async def test_enable_adds_special_payload(self, services):
        from plugins.manx.hook import enable
        await enable(services)
        services['file_svc'].add_special_payload.assert_awaited_once()
        call_args = services['file_svc'].add_special_payload.call_args[0]
        assert call_args[0] == 'manx.go'

    @pytest.mark.asyncio
    async def test_enable_no_websocket_contact_raises(self, mock_services):
        """If no websocket contact exists, enable should raise."""
        from plugins.manx.hook import enable
        mock_services['contact_svc'].contacts = [mock_services['contact_svc'].contacts[0]]
        # Only TCP contact, no websocket — the list comprehension returns empty
        with pytest.raises(IndexError):
            await enable(mock_services)
