import random, time

def poisson(rate, duration, start_time, nodes):
    data = []
    timestamp = start_time

    while timestamp<duration+start_time: 
        timestamp = timestamp + random.expovariate(rate)
        source = random.choice(nodes)
        data.append((timestamp, source.node_id))

    return data

def deterministic(rate, duration, start_time, nodes):
    data = []
    timestamp = start_time

    while timestamp<duration+start_time: 
        timestamp = timestamp + rate
        source = random.choice(nodes)
        data.append((timestamp, source.node_id))

    return data
