import time, random, numpy as np
from node import Node
from events import Proposal
from algorithms import *

class Coordinator():
    def __init__(self, params):
        self.clock = time.time()
        self.proposals = np.array([])
        self.nodes = np.array([])

        self.params = params

        if params['fork_choice_rule']=='longest-chain':
            self.global_blocktree = LongestChain()

    def add_node(self, node):
        self.nodes = np.append(self.nodes, node)

    def generate_proposals(self):
        start_time = self.clock
        timestamp = self.clock
        with open('./logs/data.log', 'w+') as f:
            f.write('Proposals:\n')
            while timestamp<self.params['duration']+start_time: 
                timestamp = timestamp + random.expovariate(self.params['proposal_rate'])
                proposal = Proposal(timestamp) 
                self.proposals = np.append(self.proposals, proposal)
                f.write(f'time: {proposal.timestamp}\n')


    def set_transactions(self, dataset):
        self.txs = np.asarray(dataset)
        with open('./logs/data.log', 'a') as f:
            f.write('Transactions:\n')
            for d in dataset:
                f.write(f'time: {d.timestamp}, id: {d.id}, source: {d.source.node_id}\n')
                self.nodes[d.source.node_id].add_to_local_txs(d)

    def update_finalized_blocks(self, timestamp):
        with open('./logs/data.log', 'a') as f:
            f.write(f'Finalized blocks at {timestamp}:\n')
            for v in self.global_blocktree.tree.vertices():
                b = self.global_blocktree.blocks[v]
                if self.global_blocktree.is_finalized(b, self.params['tx_error_prob']):
                    s = f'{b.id}:'
                    for tx in b.txs:
                        s+=f'{tx.id},'
                    s+='\n'
                    f.write(s)

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
        while tx_i<self.txs.shape[0] and p_i<self.proposals.shape[0]:
            # out of all transactions
            if tx_i==self.txs.shape[0]:
                # process proposal
                self.clock = self.proposals[p_i].timestamp
                # choose proposer uniformly at random
                proposer = random.choice(self.nodes)
                proposer.propose(self.proposals[p_i].timestamp, 
                    self.params['max_block_size'],
                    self.params['fork_choice_rule'],
                    self.params['model'])
                p_i+=1
            # out of all proposals
            elif p_i==self.proposals.shape[0]:
                tx = self.txs[tx_i]
                source_node = tx.source
                source_node.broadcast(tx, self.params['max_block_size'],
                        self.params['model'])
                self.clock = tx.timestamp
                tx_i+=1
            else:
                if self.txs[tx_i].timestamp < self.proposals[p_i].timestamp:
                    # transaction processing occurs when a node is selected to
                    # be a proposer, so don't do anything but increment
                    # transaction index and move global clock
                    tx = self.txs[tx_i]
                    source_node = tx.source
                    source_node.add_to_local_txs(tx)
                    source_node.broadcast(tx, self.params['max_block_size'],
                            self.params['model'])
                    self.clock = tx.timestamp
                    tx_i+=1
                # proposal before transaction
                else:
                    # process proposal
                    self.clock = self.proposals[p_i].timestamp
                    # choose proposer uniformly at random
                    proposer = random.choice(self.nodes)
                    proposer.propose(self.proposals[p_i],
                        self.params['max_block_size'],
                        self.params['fork_choice_rule'],
                        self.params['model'], self.global_blocktree)
                    self.update_finalized_blocks(self.proposals[p_i].timestamp)
                    p_i+=1

        # loop over all nodes and process buffer
        for node in self.nodes:
            node.process_buffer(float('Inf'))
