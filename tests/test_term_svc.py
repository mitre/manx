"""Tests for app.term_svc — TermService class."""

from unittest.mock import MagicMock, patch

import pytest

from plugins.manx.app.term_svc import TermService
from tests.conftest import FakeSocketConn


class TestTermServiceInit:

    def test_socket_conn_assigned(self, mock_services):
        svc = TermService(mock_services)
        assert svc.socket_conn is not None

    def test_socket_conn_is_tcp_contact(self, mock_services):
        svc = TermService(mock_services)
        assert svc.socket_conn.name == 'tcp'

    def test_log_created(self, mock_services):
        svc = TermService(mock_services)
        assert svc.log is not None

    def test_no_tcp_contact_raises(self):
        """If there is no TCP contact, the index will be out of range."""
        services = {
            'contact_svc': MagicMock(),
        }
        services['contact_svc'].contacts = []
        with pytest.raises(IndexError):
            TermService(services)

    def test_multiple_contacts_picks_tcp(self):
        """TermService should pick the contact whose name is 'tcp'."""
        ws = MagicMock()
        ws.name = 'websocket'
        tcp = FakeSocketConn()
        services = {
            'contact_svc': MagicMock(),
        }
        services['contact_svc'].contacts = [ws, tcp]
        svc = TermService(services)
        assert svc.socket_conn is tcp

    def test_tcp_contact_first_in_list(self):
        tcp = FakeSocketConn()
        other = MagicMock()
        other.name = 'udp'
        services = {
            'contact_svc': MagicMock(),
        }
        services['contact_svc'].contacts = [tcp, other]
        svc = TermService(services)
        assert svc.socket_conn is tcp

    def test_only_websocket_contacts(self):
        """If no TCP contact exists, should raise IndexError."""
        ws1 = MagicMock()
        ws1.name = 'websocket'
        ws2 = MagicMock()
        ws2.name = 'websocket'
        services = {
            'contact_svc': MagicMock(),
        }
        services['contact_svc'].contacts = [ws1, ws2]
        with pytest.raises(IndexError):
            TermService(services)
