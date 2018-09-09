import random, time, numpy as np
from events import Transaction

def poisson(rate, duration, start_time, nodes):
    data = []
    timestamp = start_time

    while timestamp<duration+start_time: 
        timestamp = timestamp + np.random.exponential(1.0/rate)
        tx = Transaction(timestamp, np.random.choice(nodes))
        data.append(tx)

    return data

def deterministic(rate, duration, start_time, nodes):
    data = []
    timestamp = start_time

    while timestamp<duration+start_time: 
        timestamp = timestamp + rate
        tx = Transaction(timestamp, np.random.choice(nodes))
        data.append(tx)

    return data
