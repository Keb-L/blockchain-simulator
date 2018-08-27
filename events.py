import uuid 

class Transaction():
    def __init__(self, timestamp, source):
        self.timestamp = timestamp
        self.source = source
        self.id = uuid.uuid4().hex

class Proposal():
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def set_block(self, block):
        self.block = block
