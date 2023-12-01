from app.utility.base_object import BaseObject


class Connection(BaseObject):

    def __init__(self, reader, writer):
        super().__init__()
        self.reader = reader
        self.writer = writer
