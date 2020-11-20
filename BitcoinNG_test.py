import sys
import json
import numpy as np

# Create experimental parameters and write to JSON file
import os, shutil, pprint, glob, csv

proposal_rates = [0.1]
n_trials = 1

params = {
    'Block tree proposal rate parameter': 0,
    'Block micro proposal rate parameter': 1, # 10 seconds
    'Block size (txs)': 50,
    'Transaction rate parameter': 1, # 1 second
    'Duration (sec)': 0,
    'Fork choice rule': 'BitcoinNG',
    'Network model': 'Decker-Wattenhorf',
    'Number of adversaries': 1,
    'Number of nodes': 100,
    'Probability of error in transaction confirmation': 0.01,
    'Transaction dataset': 'poisson',
    'Transaction scheduling rule': 'FIFO',
    'Logging enabled': True
 }



pp = pprint.PrettyPrinter()

print(os.getcwd())
    
for i in range(0, len(proposal_rates)):
    rate = proposal_rates[i]
    params['Block tree proposal rate parameter'] = rate
    params['Duration (sec)'] = 1000

    d = {}
    d['setting-name'] = f'bitcoin-ng-test'
    d[f'bitcoin-ng-test'] = params
    print('Parameters:')
    pp.pprint(d)
    with open('results/bitcoin_ng.json', 'w+') as outfile:
        json.dump(d, outfile)