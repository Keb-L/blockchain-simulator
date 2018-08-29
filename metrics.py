import re
from constants import TX_RATE

def compute_throughput():
    return TX_RATE

def compute_latency():
    parse_transaction = False
    d = {}
    avg_latency = 0.0
    finalized_tx_count = 0
    with open('logs/data.log') as f:
        lines = f.readlines()
        for line in lines:
            if line=='Transactions:\n':
                parse_transaction = True
            elif line.startswith('Finalized blocks at'):
                break
            elif parse_transaction:
                l = line.split(',')
                timestamp = float(l[0].split('time: ')[1])
                id = l[1].split('id: ')[1]
                d[id] = {'generation_timestamp': timestamp}
        finalization_timestamp = float(re.search('Finalized blocks at (.*):',
                lines[-1]).group(1))
        finalized_txs = lines[-1].rstrip().split(':')[1].split(',')
        for tx in finalized_txs:
            if tx in d:
                latency = finalization_timestamp-d['generation_timestamp']
                d[tx] = {'generation_timestamp': d['generation_timestamp'],
                        'finalization_timestamp': finalization_timestamp,
                        'latency': latency}
                finalized_tx_count+=1
                avg_latency+=latency

    if finalized_tx_count!=0:
        avg_latency = avg_latency/finalized_tx_count

    return avg_latency

compute_latency()
