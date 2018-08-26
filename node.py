import logging

class Node():
    def __init__(self, node_id):
        self.node_id = node_id

        self.local_txs = []
        self.local_blocktree = []
        self.orphans = set()
        self.buffer = []
        self.neighbors = []

        handler = logging.FileHandler(f'./logs/{self.node_id}.log')        

        self.logger = logging.getLogger(f'{self.node_id}')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)


    def add_neighbor(self, neighbor_node):
        self.neighbors.append(neighbor_node)

    def add_to_buffer(self, event):
        self.buffer.append(event)

    def add_to_local_txs(self, tx):
        self.logger.info('Adding %s to local transaction queue at %s',
                (tx[1].source.node_id,
            tx[1].id), tx[0]) 
        self.local_txs.append(tx)

    def broadcast(self, event):
        for neighbor in self.neighbors:
            neighbor.add_to_buffer(event)

    def propose(self, event):
        self.logger.info('Proposing at %s', event) 
