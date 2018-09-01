import logging, copy, numpy as np
from block import Block
import graph_tool.all as gt
from network import fixed_latency, decker_wattenhorf
from algorithms import *

class Node():
    def __init__(self, node_id, algorithm):
        self.node_id = node_id

        if algorithm=='longest-chain':
            self.local_blocktree = LongestChain()

        self.local_txs = np.array([])
        self.orphans = np.array([])
        self.buffer = np.array([])
        self.neighbors = np.array([])

        handler = logging.FileHandler(f'./logs/{self.node_id}.log')        

        self.logger = logging.getLogger(f'{self.node_id}')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)


    def add_neighbor(self, neighbor_node):
        self.neighbors = np.append(self.neighbors, neighbor_node)

    def add_to_buffer(self, event):
        if event.__class__.__name__=='Proposal':
            self.logger.info(f'Adding block %s to buffer', event.block.id)
        self.buffer = np.append(self.buffer, event)

    def add_to_local_txs(self, tx):
        self.local_txs = np.append(self.local_txs, tx)

    def broadcast(self, event, max_block_size, delay_model):
        for neighbor in self.neighbors:
            # add network delay
            if delay_model=='Decker-Wattenhorf':
                event.timestamp+=decker_wattenhorf(max_block_size)
            neighbor.add_to_buffer(event)

    def log_local_blocktree(self):
        self.logger.info(f'\nLocal blocktree:\n{self.local_blocktree.graph_to_str()}') 

    def process_buffer(self, timestamp):
        b_i = 0
        while b_i<len(self.buffer):
            if self.buffer[b_i].timestamp>timestamp:
                break
            event = self.buffer[b_i]
            if event.__class__.__name__=='Transaction':
                # transactions should be added to local transaction queue
                self.add_to_local_txs(event)
            elif event.__class__.__name__=='Proposal':
                # blocks should be added to local block tree
                copied_block = Block(event.block.txs, event.block.id,
                        event.block.parent_id) 
                # add block based on parent id
                parent_block = self.local_blocktree.add_block(copied_block)
                self.logger.info('%s: Block reception event. Block id: %s, Parent block: %s',
                        event.timestamp, copied_block.id, event.block.parent_id) 
                self.logger.info(f'\nLocal blocktree:\n{self.local_blocktree.graph_to_str()}') 
                if parent_block==None:
                    self.orphans = np.append(self.orphans, copied_block)
            b_i+=1
        self.buffer = self.buffer[b_i:]

        # loop over orphans repeatedly while we added an orphan block
        added_orphan_block = True
        while added_orphan_block:
            # assume we did not add an orphan block
            added_orphan_block = False
            # loop over orphans and update remaining orphans
            remaining_orphans = np.zeros(self.orphans.shape, dtype=bool)
            for i, orphan in enumerate(self.orphans):
                parent_block = self.local_blocktree.add_block(orphan)
                if parent_block==None:
                    # did not add orphan block, block remains as orphan
                    remaining_orphans[i] = True
                else:
                    # we did add an orphan block
                    added_orphan_block = True
            self.orphans = self.orphans[remaining_orphans]

        if timestamp==float('Inf'):
            self.log_local_blocktree()

    def propose(self, proposal, max_block_size, fork_choice_rule, delay_model,
            global_blocktree):
        # process propoer's buffer
        self.process_buffer(proposal.timestamp)

        # append new block to appropriate chain
        new_block = Block()

        # find all txs in main chain
        main_chain = self.local_blocktree.main_chain()
        main_chain_txs = np.array([])
        for v in main_chain:
            main_chain_txs = np.append(main_chain_txs, self.local_blocktree.blocks[v].txs)

        tx_i = 0
        tx_str = ''
        while tx_i<len(self.local_txs):
            # if we exceed current time, exit loop
            if self.local_txs[tx_i].timestamp>proposal.timestamp:
                break
            # if we exceed max block size, exit loop
            elif len(new_block.txs)>max_block_size:
                break
            elif self.local_txs[tx_i] not in main_chain_txs:
                new_block.add_tx(self.local_txs[tx_i])
                tx_str+=f'{self.local_txs[tx_i].id},'
            tx_i+=1

        self.logger.info('%s: Block proposal event. Block id: %s; Txs: %s',
                proposal.timestamp, new_block.id,
                tx_str) 

        proposal.set_block(new_block)

        # find selected chain based on schema and add block
        local_parent_block = self.local_blocktree.fork_choice_rule(new_block)
        new_block.set_parent_id(local_parent_block.id)
        
        self.logger.info(f'\nLocal blocktree:\n{self.local_blocktree.graph_to_str()}') 

        # copy block and add new block to global blocktree
        copied_block = Block(new_block.txs, new_block.id, new_block.parent_id) 
        global_parent_block = global_blocktree.add_block(copied_block)
        copied_block.set_parent_id(global_parent_block.id)

        # broadcast to rest of network
        self.broadcast(proposal, max_block_size, delay_model)
