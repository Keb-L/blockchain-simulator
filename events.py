import uuid 

class Transaction():
    def __init__(self, timestamp, source):
        self.timestamp = timestamp
        self.source = source
        self.id = uuid.uuid4().hex[0:10]

        self.main_chain_timestamp = None
        self.finalization_timestamp = None

    def set_main_chain_arrival(self, main_chain_timestamp):
        self.main_chain_timestamp = main_chain_timestamp

    def set_finalization_timestamp(self, finalization_timestamp):
        self.finalization_timestamp = finalization_timestamp

class Proposal():
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def set_block(self, block):
        self.block = block
