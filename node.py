class Node():
    def __init__(self, node_id):
        self.node_id = node_id
        self.local_txs = []
        self.local_blocktree = []
        self.orphans = set()
        self.events = []
