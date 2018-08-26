import uuid 

class Block():
    def __init__(self, parent_id):
        self.parent_id = parent_id
        self.txs = []
        self.id = uuid.uuid4().hex
        self.children = set()

    def add_tx(self, tx):
        self.txs.append(tx)

    def add_child(self, block):
        self.children.add(block)

    # recursively find longest chain and return leaf
    def longest_chain(self, length=0):
        if len(self.children)==0:
            return self, 0

        longest_chain_length = 0
        longest_chain_block = self
        for child in self.children:
            child_block, length = child.longest_chain()
            if length+1>longest_chain_length:
                longest_chain_length = length+1
                longest_chain_block = child_block
        return longest_chain_block, longest_chain_length

class Transaction():
    def __init__(self, source):
        self.source = source
        self.id = uuid.uuid4().hex
