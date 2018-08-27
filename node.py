import logging
from messages import Block
from network import fixed_latency, decker_wattenhorf

class Node():
    def __init__(self, node_id):
        self.node_id = node_id

        self.local_txs = []
        self.local_blocktree = Block(None)
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
                (tx['tx'].source.node_id,
            tx['tx'].id), tx['time']) 
        self.local_txs.append(tx)

    def broadcast(self, event, max_block_size, delay_model):
        for neighbor in self.neighbors:
            # add network delay
            if delay_model=='Decker-Wattenhorf':
                event['time']+=decker_wattenhorf(max_block_size)
            neighbor.add_to_buffer(event)

    def propose(self, current_time, max_block_size, fork_choice_rule, delay_model):
        self.logger.info('Proposing at %s', current_time) 

        # find selected chain based on schema
        if fork_choice_rule=='longest-chain':
            chain, length = self.local_blocktree.longest_chain()

        # append new block to appropriate chain
        new_block = Block(chain.id)
        chain.add_child(new_block)

        tx_i = 0
        while tx_i<len(self.local_txs):
            # if we exceed current time, exit loop
            if self.local_txs[tx_i]['time']>current_time:
                break
            # if we exceed max block size, exit loop
            elif len(new_block.txs)<max_block_size:
                break
            else:
                new_block.add_tx(self.local_txs[tx_i]['tx'])
                tx_i+=1

        # broadcast to rest of network
        self.broadcast({'time': current_time, 'block': new_block},
                max_block_size, delay_model)

        # update local transactions
        self.local_txs = self.local_txs[tx_i:]
