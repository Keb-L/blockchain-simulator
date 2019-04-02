import numpy as np, uuid

class Block():
    def __init__(self, txs=None, id=None, parent_id=None, proposal_timestamp=0,
            block_type = 'tree', referenced_blocks=None, emptiness = 0):
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


        self.pool_block_ref_timestamp = None
        self.finalization_timestamp = None
        self.emptiness = emptiness

        if referenced_blocks is None:
            self.referenced_blocks = np.array([])
        else:
            self.referenced_blocks = referenced_blocks.copy()

        self.block_type = block_type 

    def set_block_type(self, block_type, chain=0):
        self.block_type = block_type
        if self.block_type=='proposer':
            self.votes = 0
        else:
            self.block_chain = chain
            

    def add_tx(self, tx):
        self.txs = np.append(self.txs, tx)

    def set_parent_id(self, parent_id):
        self.parent_id = parent_id

    def set_pool_block_ref_timestamp(self, pool_block_ref_timestamp):
        self.pool_block_ref_timestamp = pool_block_ref_timestamp

    def set_finalization_timestamp(self, finalization_timestamp):
        self.finalization_timestamp = finalization_timestamp

    def set_emptiness(self, emptiness):
        self.emptiness = emptiness

    def add_referenced_block(self, referenced_block):
        self.referenced_blocks = np.append(self.referenced_blocks,
                referenced_block)
