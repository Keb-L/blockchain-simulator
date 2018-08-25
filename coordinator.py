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

    def process_proposal(self):
        # choose proposer uniformly at random
        proposer = random.choice(self.nodes)

        # process all relevant transactions
        proposer_txs = list(filter(lambda tx: tx[0]<self.clock and
                tx[1].source.node_id==proposer.node_id, self.txs))


    def run(self):
        tx_i = 0
        p_i = 0

        # run main loop
        while tx_i<len(self.txs) and p_i<len(self.proposals):
            # out of all transactions
            if tx_i==len(self.txs):
                p_i+=1
            # out of all proposals
            elif p_i==len(self.proposals):
                tx_i+=1
            else:
                # transaction before proposal
                if self.txs[tx_i][0] < self.proposals[p_i]:
                    # transaction processing occurs when a node is selected to
                    # be a proposer, so don't do anything but increment
                    # transaction index and move global clock
                    event = self.txs[tx_i]
                    self.clock = event[0]
                    tx_i+=1
                # proposal before transaction
                else:
                    # process proposal
                    event = self.proposals[p_i]
                    self.clock = event
                    self.process_proposal()
                    p_i+=1
        
