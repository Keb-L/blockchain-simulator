import time, random
from events import Proposal

class Coordinator():
    def __init__(self, params):
        self.clock = time.time()
        self.proposals = []
        self.txs = []
        self.nodes = []

        self.params = params

    def add_node(self, node):
        self.nodes.append(node)

    def generate_proposals(self):
        start_time = self.clock
        timestamp = self.clock
        while timestamp<self.params['duration']+start_time: 
            timestamp = timestamp + random.expovariate(self.params['proposal_rate'])
            proposal = Proposal(timestamp) 
            self.proposals.append(proposal)

    def set_transactions(self, dataset):
        self.txs = dataset
        with open('./logs/data.log', 'w+') as f:
            for d in dataset:
                f.write(f'time: {d.timestamp}, id: {d.id}, source: {d.source.node_id}\n')

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
        while tx_i<len(self.txs) and p_i<len(self.proposals):
            # out of all transactions
            if tx_i==len(self.txs):
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
            elif p_i==len(self.proposals):
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
                        self.params['model'])
                    p_i+=1
