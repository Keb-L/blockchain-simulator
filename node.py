import logging, copy, json, numpy as np
from block import *
import graph_tool.all as gt
from network import zero_latency, decker_wattenhorf, constant_decker_wattenhorf
from algorithms import *
from constants import TX_SIZE

class Node():
    def __init__(self, node_id, algorithm, tx_rule, max_block_size, location=None):
        self.node_id = node_id

        if algorithm=='longest-chain-with-pool':
            self.local_blocktree = LongestChainWithPool(block_size=max_block_size) 
        elif algorithm=='longest-chain':
            self.local_blocktree = LongestChain()
        elif algorithm=='GHOST':
            self.local_blocktree = GHOST()
        elif algorithm=='Prism':
            self.local_blocktree = Prism()
        elif algorithm=='Conflux':
            self.local_blocktree = Conflux()
            self.local_pivot_chain = None
            self.local_epochs = None
            self.local_block_order = None
        ###recheck the fork_choice_rule in prarm.json and add the local_blocktree

        self.algorithm = algorithm

        self.tx_rule = tx_rule

        self.location=location

        self.orphans = np.array([])
        self.neighbors = np.array([])
    

    def create_arrays(self, num_txs):

        self.local_tx_i = 0
        self.local_txs = np.empty(num_txs, dtype=object)

        # this is an event buffer containing broadcasted both block proposals and
        # transactions
        self.buffer = np.array([])

    def add_neighbor(self, neighbor_node):
        self.neighbors = np.append(self.neighbors, neighbor_node)

    def add_block_by_tx_rule(self, new_block, tx):
        if self.tx_rule=='FIFO':
            new_block.add_tx(tx)
        # m should range from f*delta (block proposal rate * block delay)
        # to 10*f*delta
        elif self.tx_rule=='1/m' and random.random()<1.0/(2*2.3333):
            new_block.add_tx(tx)
    
 
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
                proposal_block = event.block   #
                if self.algorithm=='longest-chain' or self.algorithm=='GHOST':
                    copied_block = Block(txs=proposal_block.txs,
                            id=proposal_block.id, parent_id=proposal_block.parent_id,
                            proposal_timestamp=proposal_block.proposal_timestamp)
                elif self.algorithm=='longest-chain-with-pool':
                    copied_block = LinkedBlock(txs=proposal_block.txs,
                            id=proposal_block.id, parent_id=proposal_block.parent_id,
                            proposal_timestamp=proposal_block.proposal_timestamp,
                            referenced_blocks=proposal_block.referenced_blocks,
                            block_type=proposal_block.block_type) 
                elif self.algorithm=='Prism':
                    copied_block = PrismBlock(txs=proposal_block.txs,
                            id=proposal_block.id, parent_id=proposal_block.parent_id,
                            proposal_timestamp=proposal_block.proposal_timestamp,
                            referenced_blocks=proposal_block.referenced_blocks,
                            block_type=proposal_block.block_type,
                            max_voted_block_depth=proposal_block.max_voted_block_depth)

                elif self.algorithm=='Conflux':
                    copied_block = ConfluxBlock(txs=proposal_block.txs,
                            id=proposal_block.id, parent_id=proposal_block.parent_id,
                            proposal_timestamp=proposal_block.proposal_timestamp,
                            ref_ids=proposal_block.ref_ids)
                    #print('cb_ref_ids',copied_block.ref_ids)
                # check if parent block is acquired yet
                # if parent block and reference blocks are found, then we can add to node's local
                # blocktree
                # if parent block of reference blocks are not found, then the block is deemed an
                # orphan
                parent_block = self.local_blocktree.get_block_by_id(copied_block.parent_id)

                absence_ref_block = False
                if self.algorithm=='Conflux':
                    ref_blocks = []
                    for j, ref_id in enumerate(copied_block.ref_ids):
                        ref_block = self.local_blocktree.get_block_by_id(ref_id)
                        
                        if ref_block is None:
                            absence_ref_block = True
                            break    
                        ref_blocks.append(ref_block)    #
                if (parent_block is None) or (absence_ref_block is True):
                    self.orphans = np.append(self.orphans, copied_block)
                else:
                    if self.algorithm=='Conflux':
                        self.local_blocktree.add_block_by_parent_references(parent_block=parent_block,
                                new_block=copied_block, ref_blocks=ref_blocks)
                    else:
                        self.local_blocktree.add_block_by_parent(parent_blocks=parent_block,
                                new_block=copied_block)
            b_i+=1

        # remove already processed items in buffer
        self.buffer = self.buffer[b_i:]
        self.buffer_i = 0 

        # loop over orphans repeatedly while we added an orphan block
        added_orphan_block = True
        while added_orphan_block:
            # assume we did not add an orphan block
            added_orphan_block = False
            # loop over orphans and update remaining orphans
            remaining_orphans = np.zeros(self.orphans.shape, dtype=bool)
            for i, block in enumerate(self.orphans):
                parent_block = self.local_blocktree.get_block_by_id(block.parent_id)
                
                absence_ref_block = False
                if self.algorithm=='Conflux':
                    # blocks referenced
                    ref_blocks = []
                    for j, ref_id in enumerate(block.ref_ids):
                        ref_block = self.local_blocktree.get_block_by_id(ref_id)
                        if ref_block is None:
                            absence_ref_block = True
                            break    
                        ref_blocks.append(ref_block)
                if (parent_block is None) or (absence_ref_block is True):
                    # cannot add orphan block, block remains as orphan
                    remaining_orphans[i] = True
                else:
                    # we can add an orphan block
                    if self.algorithm=='Conflux':
                        parent_block = self.local_blocktree.add_block_by_parent_references(
                            parent_block=parent_block, new_block=block, ref_blocks=ref_blocks)
                        added_orphan_block = True
                    else:
                        parent_block = self.local_blocktree.add_block_by_parent(parent_block=parent_block,
                            new_block=block)
                        added_orphan_block = True
            self.orphans = self.orphans[remaining_orphans]
            
    
    def propose(self, proposal, max_block_size, fork_choice_rule, delay_model):
        # process proposer's buffer
        self.process_buffer(proposal.timestamp)

        # append new block to appropriate chain
        if self.algorithm=='longest-chain' or self.algorithm=='GHOST':
            new_block = Block(proposal_timestamp=proposal.timestamp)
        elif self.algorithm=='longest-chain-with-pool':
            new_block = LinkedBlock(proposal_timestamp=proposal.timestamp,
                    block_type=proposal.proposal_type)
        elif self.algorithm=='Prism':
            new_block = PrismBlock(proposal_timestamp=proposal.timestamp)
        elif self.algorithm=='Conflux':
            new_block = ConfluxBlock(proposal_timestamp=proposal.timestamp)

        # find all txs in main chain
        if self.algorithm=='Conflux':
            all_chains_txs = np.array([])
            #'''
            pivot_chain = self.local_blocktree.random_pivot_chain()
            if len(pivot_chain) != 0:
                #print('node233', len(pivot_chain))
                epochs, block_ids = self.local_blocktree.topology_sorting(pivot_chain)
                #print('node236')
            else:
                block_ids = []
            blocks = []
            for block_id in block_ids:
                block = self.local_blocktree.get_block_by_id(block_id)
                blocks.append(block)
            all_chains_txs = np.concatenate([b.txs for b in blocks]).ravel()
            #'''
        else:
            main_chain = self.local_blocktree.random_main_chain()
            main_chain_txs = np.concatenate([b.txs for b in main_chain]).ravel()


        added_txs = 0
        if self.local_tx_i>0:
            for elem in np.nditer(self.local_txs[:self.local_tx_i],
                    flags=['refs_ok']):
                tx = elem.item()
                if tx.timestamp>proposal.timestamp:
                    # no potential txs left
                    break
                if new_block.txs.shape[0]>max_block_size:
                    # there are potential txs left on the table
                    continue

                if (tx not in all_chains_txs) and (self.algorithm=='Conflux'):
                    self.add_block_by_tx_rule(new_block, tx)
                    added_txs+=1
                elif (self.algorithm!='Conflux') and (tx not in main_chain_txs):
                    self.add_block_by_tx_rule(new_block, tx)
                    added_txs+=1


        proposal.set_block(new_block)

        if self.algorithm=='Conflux':
            self.local_blocktree.add_block_by_fork_choice_rule_conflux(new_block)
        else:
            self.local_blocktree.add_block_by_fork_choice_rule(new_block)
    
        return proposal
