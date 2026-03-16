"""Shared fixtures and mocks for manx plugin tests."""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Set up sys.path so that `plugins.manx` resolves to this repo.
# The repo lives at /tmp/manx-pytest, and imports use `plugins.manx.app...`
# We create a virtual package path:
#   /tmp/manx-pytest/..  -->  contains  plugins/manx  (symlink or path trick)
# ---------------------------------------------------------------------------
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_plugins_root = os.path.dirname(_repo_root)  # parent of manx-pytest

# We need "plugins.manx" to resolve.  Create namespace package.
sys.path.insert(0, _plugins_root)

# Ensure the 'plugins' package exists as a namespace
import importlib
if 'plugins' not in sys.modules:
    # Create a namespace package pointing to the parent dir
    import types
    plugins_pkg = types.ModuleType('plugins')
    plugins_pkg.__path__ = [os.path.join(_plugins_root)]
    plugins_pkg.__package__ = 'plugins'
    sys.modules['plugins'] = plugins_pkg

# Ensure plugins.manx points to this repo
if 'plugins.manx' not in sys.modules:
    import types
    manx_pkg = types.ModuleType('plugins.manx')
    manx_pkg.__path__ = [_repo_root]
    manx_pkg.__package__ = 'plugins.manx'
    sys.modules['plugins.manx'] = manx_pkg

# ---------------------------------------------------------------------------
# Stub out heavy Caldera imports so the plugin modules can be imported
# without pulling in the full Caldera framework.
# ---------------------------------------------------------------------------

# app.utility.base_world --------------------------------------------------
base_world_mod = MagicMock()


class _FakeBaseWorld:
    TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

    class Access:
        RED = 'red'
        BLUE = 'blue'

    @staticmethod
    def get_config(prop):
        _configs = {
            'app.contact.websocket': 'ws://localhost:7012',
        }
        return _configs.get(prop, '')

    @staticmethod
    def generate_name(size=10):
        return 'a' * size


base_world_mod.BaseWorld = _FakeBaseWorld
sys.modules.setdefault('app', MagicMock())
sys.modules['app.utility'] = MagicMock()
sys.modules['app.utility.base_world'] = base_world_mod

# app.utility.base_service -------------------------------------------------
base_service_mod = MagicMock()


class _FakeBaseService(_FakeBaseWorld):
    @staticmethod
    def add_service(name, svc):
        return MagicMock()  # logger


base_service_mod.BaseService = _FakeBaseService
sys.modules['app.utility.base_service'] = base_service_mod

# aiohttp / aiohttp_jinja2 ------------------------------------------------
if 'aiohttp' not in sys.modules:
    aiohttp_mod = MagicMock()

    class _FakeWebResponse:
        def __init__(self, data=None, **kwargs):
            self.data = data
            self.body = json.dumps(data).encode() if data else b''
            self.content_type = 'application/json'

    aiohttp_mod.web.json_response = lambda d: _FakeWebResponse(data=d)
    aiohttp_mod.web.Response = _FakeWebResponse
    sys.modules['aiohttp'] = aiohttp_mod
    sys.modules['aiohttp.web'] = aiohttp_mod.web

if 'aiohttp_jinja2' not in sys.modules:
    jinja2_mod = MagicMock()

    def _fake_template(name):
        """Decorator that just passes through the coroutine."""
        def decorator(fn):
            return fn
        return decorator

    jinja2_mod.template = _fake_template
    sys.modules['aiohttp_jinja2'] = jinja2_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeSession:
    """Mimics a TCP session object."""

    def __init__(self, session_id=1, paw='abc123'):
        self.id = session_id
        self.paw = paw


class FakeAgent:
    """Mimics a Caldera agent object."""

    def __init__(self, paw='abc123', platform='linux', executors=None):
        self.paw = paw
        self.platform = platform
        self.executors = executors or ['sh']
        self.display = dict(paw=paw, platform=platform, executors=self.executors)


class FakeAbility:
    """Mimics a Caldera ability object."""

    def __init__(self, ability_id='ability-1', name='test ability'):
        self.ability_id = ability_id
        self.name = name
        self.display = dict(ability_id=ability_id, name=name)


class FakeTcpHandler:
    """Mimics a TCP handler with sessions and send/refresh."""

    def __init__(self, sessions=None):
        self.sessions = sessions if sessions is not None else []
        self.send = AsyncMock(return_value=(0, '/home', 'output', '50ms'))
        self.refresh = AsyncMock()


class FakeSocketConn:
    """Mimics a contact with tcp_handler."""

    def __init__(self, handler=None):
        self.name = 'tcp'
        self.tcp_handler = handler or FakeTcpHandler()
        self.handler = MagicMock()
        self.handler.handles = []


class FakeWebsocketContact:
    """Mimics a websocket contact."""

    def __init__(self):
        self.name = 'websocket'
        self.handler = MagicMock()
        self.handler.handles = []


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_sessions():
    return [FakeSession(1, 'abc123'), FakeSession(2, 'def456')]


@pytest.fixture
def fake_agents():
    return [
        FakeAgent('abc123', 'linux', ['sh']),
        FakeAgent('def456', 'windows', ['psh']),
    ]


@pytest.fixture
def tcp_handler(fake_sessions):
    return FakeTcpHandler(sessions=list(fake_sessions))


@pytest.fixture
def socket_conn(tcp_handler):
    return FakeSocketConn(handler=tcp_handler)


@pytest.fixture
def websocket_contact():
    return FakeWebsocketContact()


@pytest.fixture
def mock_services(socket_conn, websocket_contact, fake_agents):
    """Build a dict of mock Caldera services."""
    data_svc = AsyncMock()
    data_svc.apply = AsyncMock()
    data_svc.locate = AsyncMock(side_effect=lambda table, match=None: [
        a for a in fake_agents if match and a.paw == match.get('paw')
    ])

    auth_svc = AsyncMock()
    file_svc = AsyncMock()
    file_svc.find_file_path = AsyncMock(return_value=('manx', '/tmp/manx-pytest/shells/manx.go'))
    file_svc.compile_go = AsyncMock()
    file_svc.add_special_payload = AsyncMock()
    file_svc.sanitize_ldflag_value = MagicMock(side_effect=lambda param, val: val)

    contact_svc = MagicMock()
    contact_svc.contacts = [socket_conn, websocket_contact]
    contact_svc.report = {'websocket': []}

    app_svc = MagicMock()
    app_svc.application = MagicMock()
    app_svc.application.router = MagicMock()
    app_svc.application.router.add_route = MagicMock()
    app_svc.application.router.add_static = MagicMock()
    app_svc.retrieve_compiled_file = AsyncMock(return_value=b'compiled_binary')

    rest_svc = AsyncMock()
    rest_svc.find_abilities = AsyncMock(return_value=[])

    services = {
        'data_svc': data_svc,
        'auth_svc': auth_svc,
        'file_svc': file_svc,
        'contact_svc': contact_svc,
        'app_svc': app_svc,
        'rest_svc': rest_svc,
        'term_svc': MagicMock(),
    }
    # Make term_svc.socket_conn point to our fake
    services['term_svc'].socket_conn = socket_conn
    return services


@pytest.fixture
def mock_request():
    """Factory for fake aiohttp requests."""
    def _make(json_data=None):
        req = AsyncMock()
        req.json = AsyncMock(return_value=json_data or {})
        return req
    return _make
