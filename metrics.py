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
        i = 0

        # get all transaction generation times
        # get all finalized blocks
        prev_fin_index = 0
        while i<len(lines):
            line = lines[i]
            if line=='Transactions:\n':
                parse_transaction = True
            elif line.startswith('Finalized blocks at'):
                parse_transaction=False
                prev_fin_index = i
            elif parse_transaction:
                l = line.split(',')
                timestamp = float(l[0].split('time: ')[1])
                id = l[1].split('id: ')[1]
                d[id] = {'generation_timestamp': timestamp}
            i+=1

        # get finalization timestamp
        finalization_timestamp = float(re.search('Finalized blocks at (.*):',
                lines[prev_fin_index]).group(1))

        # sum latencies up for all transactions
        for line in lines[prev_fin_index+1:]:
            finalized_txs = line.rstrip().split(':')[1].split(',')
            for tx in finalized_txs:
                if tx in d:
                    latency = finalization_timestamp-d[tx]['generation_timestamp']
                    d[tx] = {'generation_timestamp': d[tx]['generation_timestamp'],
                            'finalization_timestamp': finalization_timestamp,
                            'latency': latency}
                    finalized_tx_count+=1
                    avg_latency+=latency

    if finalized_tx_count!=0:
        avg_latency = avg_latency/finalized_tx_count

    return avg_latency


if __name__=='__main__':
    print(f'Transaction Throughput: {compute_throughput()} transactions/sec')
    print(f'Transaction Latency: {compute_latency()} sec/transaction')
