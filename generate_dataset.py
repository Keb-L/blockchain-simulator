import random, time
from messages import Transaction

def poisson(rate, duration, start_time, nodes):
    data = []
    timestamp = start_time

    while timestamp<duration+start_time: 
        timestamp = timestamp + random.expovariate(rate)
        tx = Transaction(random.choice(nodes))
        data.append((timestamp, tx))

    return data

def deterministic(rate, duration, start_time, nodes):
    data = []
    timestamp = start_time

    while timestamp<duration+start_time: 
        timestamp = timestamp + rate
        tx = Transaction(random.choice(nodes))
        data.append((timestamp, tx))

    return data
