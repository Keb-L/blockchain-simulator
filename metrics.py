import re, json, pprint, csv, glob
from constants import TX_RATE

def dump_params():
    print('Parameters:')
    with open(f'params.json') as f:
        contents = json.load(f)
        setting_name = contents['setting-name']
        d = contents[setting_name]
    
    pp = pprint.PrettyPrinter()
    pp.pprint(d)
    print('\n')

def compute_throughput():
    with open(f'params.json') as f:
        contents = json.load(f)
        setting_name = contents['setting-name']
        d = contents[setting_name]
        duration = d['Duration (sec)']
    with open('./logs/transactions.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        num_transactions_finalized = 0
        for row in reader:
            if row['finalization timestamp']!='None':
                num_transactions_finalized+=1

    return float(num_transactions_finalized)/duration

def compute_latency():
    with open('./logs/transactions.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        main_chain_arrival_sum = 0
        main_chain_arrival_count = 0
        pool_block_sum = 0
        pool_block_count = 0
        finalization_sum = 0
        finalization_count = 0
        for row in reader:
            if row['main chain arrival timestamp']!='None':
                main_chain_arrival_sum += float(row['main chain arrival timestamp']) - float(row['generated timestamp'])
                main_chain_arrival_count += 1
            if row['pool block timestamp']!='None':
                pool_block_sum += float(row['pool block timestamp']) - float(row['generated timestamp'])
                pool_block_count += 1
            if row['finalization timestamp']!='None':
                finalization_sum += float(row['finalization timestamp']) - float(row['main chain arrival timestamp'])
                finalization_count += 1

    avg_main_chain_arrival_latency = 0 if main_chain_arrival_count==0 else main_chain_arrival_sum/main_chain_arrival_count
    avg_pool_block_latency = 0 if pool_block_count==0 else pool_block_sum/pool_block_count
    avg_finalization_latency = 0 if finalization_count==0 else finalization_sum/finalization_count
    return avg_main_chain_arrival_latency, avg_pool_block_latency, avg_finalization_latency

def dump_results():
    print('Results:')
    avg_main_chain_arrival_latency, avg_pool_block_latency, avg_finalization_latency = compute_latency() 
    print(f'Transaction Throughput: {compute_throughput()} transactions/sec')
    print(f'Main Chain Arrival Latency: {avg_main_chain_arrival_latency} sec/transaction')
    print(f'Pool Block Latency: {avg_pool_block_latency} sec/transaction')
    print(f'Finalization Latency: {avg_finalization_latency} sec/transaction')

if __name__=='__main__':
    dump_params()
    dump_results()
