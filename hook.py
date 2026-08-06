from app.utility.base_world import BaseWorld
from plugins.manx.app.h_terminal import Handle
from plugins.manx.app.term_api import TermApi
from plugins.manx.app.tcp_patch import patch_tcp_handler

name = 'Terminal'
description = 'A toolset which supports terminal access'
address = '/plugin/manx/gui'
access = BaseWorld.Access.RED


async def enable(services):
    await services.get('data_svc').apply('sessions')
    app = services.get('app_svc').application
    term_api = TermApi(services)

    # Patch the TCP handler to fix deprecated socket API (issue #51).
    # Caldera 5.0.0 uses writer.get_extra_info('socket') which returns a
    # TransportSocket that lacks send()/recv(). This patch replaces the
    # handler methods to use asyncio StreamReader/StreamWriter instead.
    tcp_contacts = [c for c in services.get('contact_svc').contacts if c.name == 'tcp']
    if tcp_contacts:
        patch_tcp_handler(tcp_contacts[0].tcp_handler)

    udp_contact = [c for c in services.get('contact_svc').contacts if c.name == 'websocket']
    udp_contact[0].handler.handles.append(Handle(tag='manx'))

    app.router.add_static('/manx', 'plugins/manx/static/', append_version=True)
    app.router.add_route('GET', '/plugin/manx/gui', term_api.splash)
    app.router.add_route('GET', '/plugin/manx/sessions', term_api.get_sessions)
    app.router.add_route('POST', '/plugin/manx/sessions', term_api.sessions)
    app.router.add_route('POST', '/plugin/manx/history', term_api.get_history)
    app.router.add_route('POST', '/plugin/manx/ability', term_api.get_abilities)
    await services.get('file_svc').add_special_payload('manx.go', term_api.dynamically_compile)
