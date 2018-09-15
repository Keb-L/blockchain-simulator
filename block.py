import numpy as np, uuid

class Block():
    def __init__(self, txs=None, id=None, parent_id=None, proposal_timestamp=0):
        if txs is None:
            self.txs = np.array([])
        else:
            self.txs = txs.copy()
        if id is None:
            self.id = uuid.uuid4().hex[0:5] 
        else:
            self.id = id

        self.proposal_timestamp = proposal_timestamp
        self.parent_id = parent_id 

        self.optimistic_confirmation_timestamp = None
        self.finalization_timestamp = None

    def add_tx(self, tx):
        self.txs = np.append(self.txs, tx)

    def set_parent_id(self, parent_id):
        self.parent_id = parent_id

    def set_optimistic_confirmation_timestamp(self,
            optimistic_confirmation_timestamp):
        self.optimistic_confirmation_timestamp = optimistic_confirmation_timestamp

    def set_finalization_timestamp(self, finalization_timestamp):
        self.finalization_timestamp = finalization_timestamp
