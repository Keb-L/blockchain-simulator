import time, random

class Coordinator():
    def __init__(self):
        self.clock = time.time()
        self.proposals = []
        self.txs = []
        self.nodes = []

    def add_node(self, node):
        self.nodes.append(node)

    def generate_proposals(self, rate, duration):
        start_time = self.clock
        timestamp = self.clock
        while timestamp<duration+start_time: 
            timestamp = timestamp + random.expovariate(rate)
            self.proposals.append(timestamp)

    def set_transactions(self, dataset):
        self.txs = dataset

    def run(self, max_block_size):
        tx_i = 0
        p_i = 0

        # run main loop
        while tx_i<len(self.txs) and p_i<len(self.proposals):
            # out of all transactions
            if tx_i==len(self.txs):
                # process proposal
                self.clock = self.proposals[p_i]
                # choose proposer uniformly at random
                proposer = random.choice(self.nodes)
                proposer.propose(self.proposals[p_i], max_block_size)
                p_i+=1
            # out of all proposals
            elif p_i==len(self.proposals):
                tx = self.txs[tx_i]
                source_node = tx[1].source
                source_node.broadcast(tx)
                self.clock = tx[0]
                tx_i+=1
            else:
                if self.txs[tx_i][0] < self.proposals[p_i]:
                    # transaction processing occurs when a node is selected to
                    # be a proposer, so don't do anything but increment
                    # transaction index and move global clock
                    tx = self.txs[tx_i]
                    source_node = tx[1].source
                    source_node.add_to_local_txs(tx)
                    source_node.broadcast(tx)
                    self.clock = tx[0]
                    tx_i+=1
                # proposal before transaction
                else:
                    # process proposal
                    self.clock = self.proposals[p_i]
                    # choose proposer uniformly at random
                    proposer = random.choice(self.nodes)
                    proposer.propose(self.proposals[p_i], max_block_size)
                    p_i+=1
