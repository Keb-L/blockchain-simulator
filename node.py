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
        self.orphans = set()
        self.buffer = np.array([])
        self.neighbors = np.array([])

        handler = logging.FileHandler(f'./logs/{self.node_id}.log')        

        self.logger = logging.getLogger(f'{self.node_id}')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)


    def add_neighbor(self, neighbor_node):
        self.neighbors = np.append(self.neighbors, neighbor_node)

    def add_to_buffer(self, event):
        self.buffer = np.append(self.buffer, event)

    def add_to_local_txs(self, tx):
        self.logger.info('Adding %s to local transaction queue at %s',
                (tx.source.node_id, tx.id), tx.timestamp) 

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
                copied_block = Block(event.block.txs, event.block.id) 
                # find selected chain based on schema
                self.local_blocktree.fork_choice_rule(copied_block)
                self.logger.info('Received and added new block %s at %s',
                        copied_block.id,
                        event.timestamp) 
            b_i+=1
        self.buffer = self.buffer[b_i:]

        if timestamp==float('Inf'):
            self.log_local_blocktree()


    def propose(self, proposal, max_block_size, fork_choice_rule, delay_model,
            global_blocktree):
        # process propoer's buffer
        self.process_buffer(proposal.timestamp)

        # append new block to appropriate chain
        new_block = Block()
        # find selected chain based on schema
        self.local_blocktree.fork_choice_rule(new_block)

        # find all txs in main chain
        main_chain = self.local_blocktree.main_chain()
        main_chain_txs = np.array([])
        for v in main_chain:
            main_chain_txs = np.append(main_chain_txs, self.local_blocktree.blocks[v].txs)

        self.logger.info('Proposing new block %s at %s', new_block.id,
                proposal.timestamp) 

        tx_i = 0
        while tx_i<len(self.local_txs):
            # if we exceed current time, exit loop
            if self.local_txs[tx_i].timestamp>proposal.timestamp:
                break
            # if we exceed max block size, exit loop
            elif len(new_block.txs)>max_block_size:
                break
            elif self.local_txs[tx_i] not in main_chain_txs:
                new_block.add_tx(self.local_txs[tx_i])
                tx_i+=1

        proposal.set_block(new_block)

        # add new block to global blocktree
        global_blocktree.fork_choice_rule(new_block)
        # broadcast to rest of network
        self.broadcast(proposal, max_block_size, delay_model)

        # update local transactions
        self.local_txs = self.local_txs[tx_i:]
