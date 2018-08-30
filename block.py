import numpy as np, uuid

class Block():
    def __init__(self, txs=None, id=None):
        if txs is None:
            self.txs = np.array([])
        else:
            self.txs = txs.copy()
        if id is None:
            self.id = uuid.uuid4().hex[0:3] 
        else:
            self.id = id

    def add_tx(self, tx):
        self.txs = np.append(self.txs, tx)
