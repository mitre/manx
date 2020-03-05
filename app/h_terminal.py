import json

from datetime import datetime


class Handle:

    def __init__(self, tag):
        self.tag = tag

    @staticmethod
    async def run(socket, path, services):
        session_id = path.split('/')[2]
        cmd = await socket.recv()
        handler = services.get('term_svc').socket_conn.tcp_handler
        paw = next(i.paw for i in handler.sessions if i.id == int(session_id))
        services.get('contact_svc').report['websocket'].append(
            dict(paw=paw, date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), cmd=cmd)
        )
        status, pwd, reply = await handler.send(session_id, cmd)
        await socket.send(json.dumps(dict(response=reply.strip(), pwd=pwd)))
