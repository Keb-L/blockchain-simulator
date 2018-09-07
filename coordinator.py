import time, random, csv, numpy as np
from node import Node
from events import Proposal
from algorithms import *
from graph_tool.all import *

class Coordinator():
    def __init__(self, params):
        self.clock = time.time()
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
        start_time = self.clock
        timestamp = self.clock
        while timestamp<self.params['duration']+start_time: 
            timestamp = timestamp + random.expovariate(self.params['proposal_rate'])
            proposal = Proposal(timestamp) 
            self.proposals = np.append(self.proposals, proposal)

    def log_global_blocktree(self):
        with open('./logs/global_blocktree.log', 'w+') as f:
            f.write(f'{self.global_blocktree.graph_to_str()}') 

    def log_txs(self):
        with open('./logs/transactions.csv', 'w', newline='') as csvfile:
            fieldnames = ['id', 'Source Node', 'Arrival Timestamp', 'Main Chain Arrival Timestamp', 'Finalization Timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for tx in self.txs:
                writer.writerow({'id': f'{tx.id}', 'Source Node':
                    f'{tx.source.node_id}', 'Arrival Timestamp':
                    f'{tx.timestamp}', 'Main Chain Arrival Timestamp':
                    f'{tx.main_chain_timestamp}', 'Finalization Timestamp':
                    f'{tx.finalization_timestamp}'})

    def log_proposals(self):
        with open('./logs/proposals.csv', 'w', newline='') as csvfile:
            fieldnames = ['Timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for p in self.proposals:
                writer.writerow({'Timestamp': f'{p.timestamp}'})


    def set_transactions(self, dataset):
        self.txs = np.asarray(dataset)

    def update_finalized_blocks(self, timestamp):
        for v in self.global_blocktree.tree.vertices():
            b = self.global_blocktree.blocks[v]
            if self.params['fork_choice_rule']=='longest-chain':
                is_finalized = self.global_blocktree.is_finalized(b, self.params)
            if is_finalized:
                for tx in b.txs:
                    tx.set_finalization_timestamp(timestamp)

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
            if (tx_i+p_i)%100==0:
                print(float(tx_i+p_i)/(self.txs.shape[0]+self.proposals.shape[0]))
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
                self.update_finalized_blocks(self.proposals[p_i].timestamp)
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
        
        self.log_txs()
        self.log_proposals()
        self.log_global_blocktree()
        graph_draw(self.global_blocktree.tree,
                vertex_text=self.global_blocktree.tree.vertex_index,
                vertex_size=50,
                vertex_font_size=15, output_size=(4200, 4200),
                edge_pen_width=1.0,
                output="global-blocktree.png")

        # ******* 
        # Commenting this out for now: since our metrics are calculated from the global tree, we don't actually need the local blocktrees to be up to date at the end of the simulation. If we were computing metrics from the local blocktrees, we would need to cut off the buffer processing at time 'duration', otherwise all the nodes would have the same local blocktree
        # *********
        # loop over all nodes and process buffer
        # for node in self.nodes:
            # node.process_buffer(self.params['duration'])
