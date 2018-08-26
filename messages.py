import uuid 

class Block():
    def __init__(self, parent_id):
        self.parent_id = parent_id
        self.txs = []
        self.id = hasher.sha256()


class Transaction():
    def __init__(self, source):
        self.source = source
        self.id = uuid.uuid4().hex
