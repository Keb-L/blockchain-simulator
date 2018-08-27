import logging, copy
from blocktree import Block
from network import fixed_latency, decker_wattenhorf

class Node():
    def __init__(self, node_id):
        self.node_id = node_id

        self.local_txs = []
        self.local_blocktree = Block()
        self.orphans = set()
        self.buffer = []
        self.neighbors = []

        handler = logging.FileHandler(f'./logs/{self.node_id}.log')        

        self.logger = logging.getLogger(f'{self.node_id}')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)


    def add_neighbor(self, neighbor_node):
        self.neighbors.append(neighbor_node)

    def add_to_buffer(self, event):
        self.buffer.append(event)

    def add_to_local_txs(self, tx):
        self.logger.info('Adding %s to local transaction queue at %s',
                (tx.source.node_id, tx.id), tx.timestamp) 
        self.local_txs.append(tx)

    def broadcast(self, event, max_block_size, delay_model):
        for neighbor in self.neighbors:
            # add network delay
            if delay_model=='Decker-Wattenhorf':
                event.timestamp+=decker_wattenhorf(max_block_size)
            neighbor.add_to_buffer(event)

    def process_buffer(self, timestamp):
        b_i = 0
        while b_i<len(self.buffer):
            if self.buffer[b_i].timestamp>timestamp:
                break
            event = self.buffer[b_i]
            if event.__class__.__name__=='Transaction':
                # transactions should be added to local transaction queue
                self.add_to_local_txs(event)
            elif event._class__.__name__=='Proposal':
                # blocks should be added to local block tree
                self.logger.info('Adding %s to local transaction queue at %s',
                        (tx.source.node_id, tx.id), tx.timestamp) 
                copied_block = copy.deepcopy(event.block) 
                # find selected chain based on schema
                if fork_choice_rule=='longest-chain':
                    chain, length = self.local_blocktree.longest_chain()
                copied_block.set_parent_id(chain.id)
                chain.add_child(copied_block)
                self.logger.info('Received and added new block %s at %s',
                        copied_block.id,
                        event.timestamp) 
            b_i+=1
        self.buffer = self.buffer[b_i:]


    def propose(self, proposal, max_block_size, fork_choice_rule, delay_model):

        # process propoer's buffer
        self.process_buffer(proposal.timestamp)

        # find selected chain based on schema
        if fork_choice_rule=='longest-chain':
            chain, length = self.local_blocktree.longest_chain()

        # append new block to appropriate chain
        new_block = Block()
        new_block.set_parent_id(chain.id)
        chain.add_child(new_block)

        tx_i = 0
        while tx_i<len(self.local_txs):
            # if we exceed current time, exit loop
            if self.local_txs[tx_i].timestamp>proposal.timestamp:
                break
            # if we exceed max block size, exit loop
            elif len(new_block.txs)<max_block_size:
                break
            else:
                new_block.add_tx(self.local_txs[tx_i])
                tx_i+=1

        proposal.set_block(new_block)
        self.logger.info('Proposing new block %s at %s', new_block.id,
                proposal.timestamp) 

        # broadcast to rest of network
        self.broadcast(proposal, max_block_size, delay_model)

        # update local transactions
        self.local_txs = self.local_txs[tx_i:]
