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

        self.orphans = np.array([])
        # this is an event buffer containing broadcasted both block proposals and
        # transactions
        self.neighbors = np.array([])

    def create_arrays(self, num_txs):
        self.local_tx_i = 0
        self.local_txs = np.empty(num_txs, dtype=object)
        self.buffer = np.array([])

    def add_neighbor(self, neighbor_node):
        self.neighbors = np.append(self.neighbors, neighbor_node)

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
            neighbor.buffer = np.append(neighbor.buffer, event)

    def add_orphan_blocks(self):
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
            self.orphans = self.orphans[remaining_orphans]

    def process_buffer(self, timestamp):
        b_i = 0 
        while b_i<len(self.buffer):
            if self.buffer[b_i].timestamp>timestamp:
                break
            event = self.buffer[b_i]
            if event.__class__.__name__=='Transaction':
                # transactions should be added to local transaction queue
                self.local_txs[self.local_tx_i] = event
                self.local_tx_i+=1
            elif event.__class__.__name__=='Proposal':
                if event.block.block_type=='tree':
                    # tree blocks should be added to local block tree
                    copied_block = Block(event.block.txs, event.block.id,
                            event.block.parent_id,
                            proposal_timestamp=event.timestamp) 
                    # add block based on parent id
                    parent_block = self.local_blocktree.add_block_by_parent_id(copied_block)
                    if parent_block==None:
                        self.orphans = np.append(self.orphans, event)
                elif event.block.block_type=='pool':
                    # blocks should be added to local block tree
                    copied_block = Block(event.block.txs, event.block.id,
                            proposal_timestamp=event.timestamp) 
                    self.local_blocktree.add_pool_block(copied_block)

            b_i+=1

        # remove already processed items in buffer
        self.buffer = self.buffer[b_i:]
        self.buffer_i = 0 

        self.add_orphan_blocks()


    def propose(self, proposal, max_block_size, fork_choice_rule, delay_model,
            global_blocktree):
        # process proposer's buffer
        self.process_buffer(proposal.timestamp)

        # append new block to appropriate chain
        new_block = Block(proposal_timestamp=proposal.timestamp,
                block_type=proposal.proposal_type)

        # find all txs in main chain
        main_chain = self.local_blocktree.random_main_chain()
        main_chain_txs = np.concatenate([b.txs for b in main_chain]).ravel()

        if self.local_tx_i>0:
            for elem in np.nditer(self.local_txs[:self.local_tx_i],
                    flags=['refs_ok']):
                tx = elem.item()
                if tx.timestamp>proposal.timestamp or new_block.txs.shape[0]>max_block_size:
                    break
                if tx not in main_chain_txs:
                    new_block.add_tx(tx)


        proposal.set_block(new_block)
        if proposal.proposal_type=='pool':
            self.local_blocktree.add_pool_block(new_block)
        elif proposal.proposal_type=='tree':
            # find selected chain based on schema and add block
            local_parent_block = self.local_blocktree.add_block_by_fork_choice_rule(new_block)
            new_block.set_parent_id(local_parent_block.id)
            
            # copy block and add new block to global blocktree
            copied_block = Block(txs=new_block.txs, id=new_block.id, parent_id=new_block.parent_id,
                    proposal_timestamp=new_block.proposal_timestamp,
                    referenced_blocks=new_block.referenced_blocks) 
            global_parent_block = global_blocktree.add_block_by_parent_id(copied_block)
            copied_block.set_parent_id(global_parent_block.id)
    
        return proposal
