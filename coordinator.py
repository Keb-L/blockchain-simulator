import random, csv, os, numpy as np
from node import Node
from events import Proposal
from algorithms import *
from logger import log_local_blocktree, log_global_blocktree, log_txs, log_statistics, draw_global_blocktree

class Coordinator():
    def __init__(self, params):
        self.proposals = np.array([])
        self.nodes = np.array([])
        self.txs = np.array([])

        self.params = params

        if params['fork_choice_rule']=='longest-chain':
            self.global_blocktree = LongestChain()
        elif params['fork_choice_rule']=='GHOST':
            self.global_blocktree = GHOST()

    def add_node(self, node):
        self.nodes = np.append(self.nodes, node)

    def generate_proposals(self):
        start_time = 0
        timestamp = 0
        while timestamp<self.params['duration']+start_time: 
            timestamp = timestamp + np.random.exponential(1.0/self.params['proposal_rate'])
            proposal = Proposal(timestamp) 
            self.proposals = np.append(self.proposals, proposal)


    def set_transactions(self, dataset):
        self.txs = np.asarray(dataset)

    def set_timestamps(self):
        # get main chain
        main_chain = self.global_blocktree.main_chain()

        # initialize vertex depth to 0 and get finalization depth
        finalization_depth = self.global_blocktree.compute_k(self.params['tx_error_prob'],
                self.params['num_nodes'], self.params['num_adversaries'])

        for depth in range(0, len(main_chain)):
            if depth+finalization_depth>len(main_chain)-1:
                break
            else:
                # top block is block depth blocks deep on main chain
                top_block = self.global_blocktree.vertex_to_blocks[main_chain[depth]]
                # bottom block is block depth+finalization_depth blocks deep on
                # main chain
                bottom_block = self.global_blocktree.vertex_to_blocks[main_chain[depth+finalization_depth]]

                # top block's finalization timestamp is bottom block's proposal
                # timestamp
                top_block.set_finalization_timestamp(bottom_block.proposal_timestamp)
                # set main chain arrival and finalization timestamp of all transactions in top block
                for tx in top_block.txs:
                    tx.set_main_chain_arrival_timestamp(top_block.proposal_timestamp)
                    tx.set_finalization_timestamp(top_block.finalization_timestamp)

    '''
    Main simulation function
    Coordinator checks head of proposal and tx queue and processes earlier
    occurring event
        - Coordinator moves global clock to next event timestamp
        - If event is a proposal
            - Choose a node uniformly at random
            - Chosen node calls propose()
        - If event is a tx
            - Broadcast tx from source node
        - After main loop, loop over all all nodes and process buffer
    '''
    def run(self):
        tx_i = 0
        p_i = 0

        # run main loop
        while tx_i<self.txs.shape[0] or p_i<self.proposals.shape[0]:
            if (tx_i+p_i)%100==0:
                print(float(tx_i+p_i)/(self.txs.shape[0]+self.proposals.shape[0]))
            # still have valid txs and proposals
            if tx_i<self.txs.shape[0] and p_i<self.proposals.shape[0]:
                # transaction before proposal
                if self.txs[tx_i].timestamp < self.proposals[p_i].timestamp:
                    # transaction processing occurs when a node is selected to
                    # be a proposer, so don't do anything but increment
                    # transaction index and move global clock
                    tx = self.txs[tx_i]
                    source_node = tx.source
                    source_node.add_to_local_txs(tx)
                    source_node.broadcast(tx, self.params['max_block_size'],
                            self.params['model'])
                    tx_i+=1
                # proposal before transaction
                else:
                    # choose proposer uniformly at random
                    proposer = random.choice(self.nodes)
                    proposal = proposer.propose(self.proposals[p_i],
                        self.params['max_block_size'],
                        self.params['fork_choice_rule'],
                        self.params['model'], self.global_blocktree)
                    # broadcast to rest of network
                    proposer.broadcast(proposal, self.params['max_block_size'],
                            self.params['model'])
                    p_i+=1
            # out of all proposals
            elif p_i==self.proposals.shape[0]:
                tx = self.txs[tx_i]
                source_node = tx.source
                source_node.broadcast(tx, self.params['max_block_size'],
                        self.params['model'])
                tx_i+=1
            # out of all transactions
            elif tx_i==self.txs.shape[0]:
                # choose proposer uniformly at random
                proposer = random.choice(self.nodes)
                proposal = proposer.propose(self.proposals[p_i], 
                    self.params['max_block_size'],
                    self.params['fork_choice_rule'],
                    self.params['model'], self.global_blocktree)
                # broadcast to rest of network
                proposer.broadcast(proposal, self.params['max_block_size'],
                        self.params['model'])
                p_i+=1

        self.set_timestamps()
        log_txs(self.txs)

        for node in self.nodes:
            log_local_blocktree(node)
        log_global_blocktree(self.global_blocktree)
        log_statistics(self.params, self.global_blocktree)
        draw_global_blocktree(self.global_blocktree)

        os.system('cat ./logs/stats.csv')

        # ******* 
        # Commenting this out for now: since our metrics are calculated from the global tree, we don't actually need the local blocktrees to be up to date at the end of the simulation. If we were computing metrics from the local blocktrees, we would need to cut off the buffer processing at time 'duration', otherwise all the nodes would have the same local blocktree
        # *********
        # loop over all nodes and process buffer
        for node in self.nodes:
            node.process_buffer(self.params['duration'])
