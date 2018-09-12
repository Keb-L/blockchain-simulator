import uuid 

class Transaction():
    def __init__(self, timestamp, source):
        self.timestamp = timestamp
        self.source = source
        self.id = uuid.uuid4().hex[0:10]

        self.main_chain_timestamp = None
        self.finalization_timestamp = None
        self.optimistic_confirmation_time = None

    def set_main_chain_arrival_timestamp(self, main_chain_timestamp):
        self.main_chain_timestamp = main_chain_timestamp

    def set_finalization_timestamp(self, finalization_timestamp):
        self.finalization_timestamp = finalization_timestamp

    def set_optimistic_confirmation_time(self, optimistic_confirmation_time ):
        self.optimistic_confirmation_time = optimistic_confirmation_time 

class Proposal():
    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.id = uuid.uuid4().hex[0:6]

    def set_block(self, block):
        self.block = block
