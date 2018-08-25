import time

class Coordinator():
    def __init__(self):
        self.clock = time.time()
        self.proposals = []
        self.txs = []

        self.nodes = []

    def add_node(self, node):
        self.nodes.append(node)
