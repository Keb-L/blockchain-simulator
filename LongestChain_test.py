import numpy as np
import sys
import json
import os, shutil, pprint, glob, csv

proposal_rates = np.linspace(0.1, 0.5, 5)
n_trials = 1


# Create experimental parameters and write to JSON file

params = {'Block proposal rate parameter': 0,
 'Block size (txs)': 50,
 'Duration (sec)': 0,
 'Fork choice rule': 'longest-chain',
 'Network model': 'Decker-Wattenhorf',
 'Number of adversaries': 1,
 'Number of nodes': 100,
 'Probability of error in transaction confirmation': 0.01,
 'Transaction dataset': 'poisson',
 'Transaction scheduling rule': 'FIFO',
 'Logging enabled': True}

pp = pprint.PrettyPrinter()

import metrics

throughputs = {}
main_chain_arrival_latencies = {}
finalization_latencies = {}

print(os.getcwd())
    
for i in range(0, len(proposal_rates)):
    rate = proposal_rates[i]
    params['Block proposal rate parameter'] = rate
    params['Duration (sec)'] = 1000
    d = {}
    d['setting-name'] = f'longest-chain-test'
    d[f'longest-chain-test'] = params
    print('Parameters:')
    pp.pprint(d)
    with open('results/longest_chain.json', 'w+') as outfile:
        json.dump(d, outfile)
