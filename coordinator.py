class Coordinator():
    def __init__(self):
        self.proposals = []
        self.txs = []

        self.nodes = []

    def add_node(self, node):
        self.nodes.append(node)
