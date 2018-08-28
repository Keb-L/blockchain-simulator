import numpy as np, uuid

class Block():
    def __init__(self):
        self.txs = np.array([])
        self.id = uuid.uuid4().hex
        self.children = set()

    def add_tx(self, tx):
        self.txs.append(tx)
