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
                    # process transaction
                    event = self.txs[tx_i]
                    tx_i+=1
                # proposal before transaction
                else:
                    # process proposal
                    event = self.proposals[p_i]
                    p_i+=1
                print(event)
        
