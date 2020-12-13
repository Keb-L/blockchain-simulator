import numpy as np

'''
Simple model of simple latency of 0 sec
'''
def zero_latency():
    return 0
'''
An approximation of network latency in the Bitcoin network based on the
following paper: https://ieeexplore.ieee.org/document/6688704/.

From the green line in Fig 1, we can approximate the function as:

    Network latency (sec) = 19/300 sec/KB * KB + 1 sec
    If we assume a transaction is 500 bytes or 1/2 KB, we get the function

    Network latency (sec) = 19/600 sec/tx * tx + 1 sec

We use this as a parameter into our exponential delay
'''
def decker_wattenhorf(msg_size):
    from constants import SEC_PER_TRANSACTION
    delta = SEC_PER_TRANSACTION * msg_size
    return np.random.exponential(delta)

'''
A constant delta value used for testing purposes
'''
def constant_decker_wattenhorf(msg_size):
    from constants import SEC_PER_TRANSACTION
    delta = SEC_PER_TRANSACTION * msg_size
    return delta
