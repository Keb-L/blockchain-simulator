import time, random

def poisson(q, size, nodes):
    intervals = [random.expovariate(q) for i in range(size)]
    timestamp = time.time()
    data = []
    for t in intervals:
        timestamp = timestamp+t
        source = random.choice(nodes)
        data.append((timestamp, source.node_id))
    return data

def deterministic(q, size, nodes):
    timestamp = time.time()
    data = []
    for t in range(0, size):
        timestamp = timestamp+t
        source = random.choice(nodes)
        data.append((timestamp, source.node_id))
    return data
