import logging, copy, numpy as np
from block import Block
import graph_tool.all as gt
from network import zero_latency, decker_wattenhorf, constant_decker_wattenhorf
from algorithms import *
from constants import TX_SIZE

class Node():
    def __init__(self, node_id, algorithm, location=None):
        self.node_id = node_id

        if algorithm=='longest-chain-with-pool':
            self.local_blocktree = LongestChainWithPool() 
        elif algorithm=='longest-chain':
            self.local_blocktree = LongestChain()
        elif algorithm=='GHOST':
            self.local_blocktree = GHOST()

        self.location=location

        self.local_txs = np.array([])
        self.orphans = np.array([])
        # this is an event buffer containing broadcasted both block proposals and
        # transactions
        self.buffer = np.array([])
        self.neighbors = np.array([])

    def add_neighbor(self, neighbor_node):
        self.neighbors = np.append(self.neighbors, neighbor_node)

    def add_to_buffer(self, event):
        self.buffer = np.append(self.buffer, event)

    def add_to_local_txs(self, tx):
        self.local_txs = np.append(self.local_txs, tx)

    def broadcast(self, event, max_block_size, delay_model):
        if event.__class__.__name__=='Transaction':
            msg_size = TX_SIZE
        elif event.__class__.__name__=='Proposal':
            msg_size = max_block_size

        # add network delay
        if delay_model=='Decker-Wattenhorf':
            delay = decker_wattenhorf(msg_size)
        elif delay_model=='Constant-Decker-Wattenhorf':
            delay = constant_decker_wattenhorf(msg_size)
        elif delay_model=='Zero':
            delay = zero_latency()

        event.timestamp+=delay

        for neighbor in self.neighbors:
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
            elif event.__class__.__name__=='Proposal':
                # blocks should be added to local block tree
                copied_block = Block(event.block.txs, event.block.id,
                        event.block.parent_id) 
                # add block based on parent id
                parent_block = self.local_blocktree.add_block_by_parent_id(copied_block)
                if parent_block==None:
                    self.orphans = np.append(self.orphans, event)
            b_i+=1

        # remove already processed items in buffer
        self.buffer = self.buffer[b_i:]

        # loop over orphans repeatedly while we added an orphan block
        added_orphan_block = True
        while added_orphan_block:
            # assume we did not add an orphan block
            added_orphan_block = False
            # loop over orphans and update remaining orphans
            remaining_orphans = np.zeros(self.orphans.shape, dtype=bool)
            for i, proposal in enumerate(self.orphans):
                parent_block = self.local_blocktree.add_block_by_parent_id(proposal.block)
                if parent_block==None:
                    # did not add orphan block, block remains as orphan
                    remaining_orphans[i] = True
                else:
                    # we did add an orphan block
                    added_orphan_block = True
                    # get new main chain
                    new_main_chain = list(map(vertex_to_blocks,
                        self.local_blocktree.main_chain()))
                    new_main_chain_ids = list(map(blocks_to_ids,
                        new_main_chain))
            self.orphans = self.orphans[remaining_orphans]

    def propose(self, proposal, max_block_size, fork_choice_rule, delay_model,
            global_blocktree):
        # process proposer's buffer
        self.process_buffer(proposal.timestamp)

        # append new block to appropriate chain
        new_block = Block(proposal_timestamp=proposal.timestamp)

        # find all txs in main chain
        main_chain = self.local_blocktree.random_main_chain()
        main_chain_txs = np.array([])
        for v in main_chain:
            main_chain_txs = np.append(main_chain_txs,
                    self.local_blocktree.vertex_to_blocks[v].txs)

        tx_i = 0
        while tx_i<len(self.local_txs):
            # if we exceed current time, exit loop
            if self.local_txs[tx_i].timestamp>proposal.timestamp:
                break
            # if we exceed max block size, exit loop
            elif len(new_block.txs)>max_block_size:
                break
            elif self.local_txs[tx_i] not in main_chain_txs:
                self.local_txs[tx_i].set_main_chain_arrival_timestamp(proposal.timestamp)
                new_block.add_tx(self.local_txs[tx_i])
            tx_i+=1

        proposal.set_block(new_block)

        if proposal.proposal_type=='pool':
            self.add_pool_block(new_block)
        elif proposal.proposal_type=='tree':
            # find selected chain based on schema and add block
            local_parent_block = self.local_blocktree.add_block_by_fork_choice_rule(new_block)
            new_block.set_parent_id(local_parent_block.id)
            
            # copy block and add new block to global blocktree
            copied_block = Block(txs=new_block.txs, id=new_block.id, parent_id=new_block.parent_id,
                    proposal_timestamp=new_block.proposal_timestamp) 
            global_parent_block = global_blocktree.add_block_by_parent_id(copied_block)
            copied_block.set_parent_id(global_parent_block.id)

        return proposal
