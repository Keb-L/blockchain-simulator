import numpy as np, uuid

class Block():
    def __init__(self, txs=None, id=None, parent_id=None, proposal_timestamp=0,
            block_type = 'tree', depth=0):
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
        self.finalization_timestamp = None
        self.depth = depth

        self.block_type = block_type 
    def set_depth(self, depth):
        self.depth = depth 

    def add_tx(self, tx):
        self.txs = np.append(self.txs, tx)

    def set_parent_id(self, parent_id):
        self.parent_id = parent_id
            
    
    def set_finalization_timestamp(self, finalization_timestamp):
        self.finalization_timestamp = finalization_timestamp


class LinkedBlock(Block):
    def __init__(self, txs=None, id=None, parent_id=None, proposal_timestamp=0,
            block_type = 'tree', referenced_blocks=None):
        super(LinkedBlock, self).__init__(txs, id, parent_id, proposal_timestamp,
                block_type)

        if referenced_blocks is None:
            self.referenced_blocks = np.array([])
        else:
            self.referenced_blocks = referenced_blocks.copy()

    def add_referenced_block(self, referenced_block):
        self.referenced_blocks = np.append(self.referenced_blocks,
                referenced_block)

class PrismBlock(LinkedBlock):
    def __init__(self, txs=None, id=None, parent_id=None, proposal_timestamp=0,
            block_type = 'proposer', referenced_blocks=None,
            max_voted_block_depth=0):

        super(PrismBlock, self).__init__(txs, id, parent_id, proposal_timestamp,
                block_type, referenced_blocks)

        self.max_voted_block_depth = max_voted_block_depth

    def set_block_type(self, block_type, chain=0):
        self.block_type = block_type
        if self.block_type=='voter':
            self.block_chain = chain

    def set_max_voted_block_depth(self, max_voted_block_depth):
        self.max_voted_block_depth = max_voted_block_depth

class ConfluxBlock(Block):
    def __init__(
        self, txs=None, id=None, parent_id=None, proposal_timestamp=0,
        block_type = 'tree', ref_ids=None):

        super(ConfluxBlock, self).__init__(txs, id, parent_id, proposal_timestamp)
        self.ref_ids = ref_ids
            
    def set_ref_ids(self, ref_blocks):
        ref_ids = []
        for ref_block in ref_blocks:
            ref_ids.append(ref_block.id)
        self.ref_ids = ref_ids

    def add_referenced_block(self, referenced_block):
        self.referenced_blocks = np.append(self.referenced_blocks,
                referenced_block)
