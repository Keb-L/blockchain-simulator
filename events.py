import uuid 

class Transaction():
    def __init__(self, timestamp, source):
        self.timestamp = timestamp
        self.source = source
        self.id = uuid.uuid4().hex[0:10]

        self.main_chain_timestamp = None
        self.confirmation_timestamp = None

    def set_main_chain_arrival(self, main_chain_timestamp):
        self.main_chain_timestamp = main_chain_timestamp

    def set_confirmation_timestamp(self, confirmation_timestamp):
        self.confirmation_timestamp = confirmation_timestamp

class Proposal():
    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.main_chain_timestamp = None
        self.confirmation_timestamp = None

    def set_block(self, block):
        self.block = block

    def set_main_chain_arrival(self, main_chain_timestamp):
        self.main_chain_timestamp = main_chain_timestamp

    def set_confirmation_timestamp(self, confirmation_timestamp):
        self.confirmation_timestamp = confirmation_timestamp
