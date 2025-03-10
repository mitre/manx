from app.utility.base_object import BaseObject
from plugins.manx.app.c_connection import Connection


class Session(BaseObject):

    @property
    def unique(self):
        return self.hash('%s' % self.paw)

    def __init__(self, id, paw, connection: Connection):
        super().__init__()
        self.id = id
        self.paw = paw
        self.connection = connection

    def store(self, ram):
        existing = self.retrieve(ram['sessions'], self.unique)
        if not existing:
            ram['sessions'].append(self)
            return self.retrieve(ram['sessions'], self.unique)
        return existing
