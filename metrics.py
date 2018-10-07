import sys, re, json, pprint, csv, glob
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

def compute_emptiness(foldername='logs'):
    emptiness_sum = 0
    emptiness_count = 0
    with open(f'{foldername}/blocks.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 'emptiness' in row:
                emptiness_sum+=int(row['emptiness'])
                emptiness_count+=1
    return float(emptiness_sum)/emptiness_count

def compute_throughputs(foldername='logs'):
    with open(f'params.json') as f:
        contents = json.load(f)
        setting_name = contents['setting-name']
        d = contents[setting_name]
        duration = d['Duration (sec)']
    with open(f'{foldername}/transactions.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        num_transactions_finalized = 0
        num_unique_transactions_finalized = 0
        for row in reader:
            if row['finalization timestamps']!='None':
                num_unique_transactions_finalized+=1
                if ';' in row['finalization timestamps']:
                    num_transactions_finalized+=len(row['finalization timestamps'].split(';'))

    return float(num_transactions_finalized)/duration, float(num_unique_transactions_finalized)/duration

def compute_latency(foldername='logs'):
    with open(f'{foldername}/transactions.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        pool_block_arr_sum = 0
        pool_block_arr_count = 0
        pool_block_ref_sum = 0
        pool_block_ref_count = 0
        main_chain_arrival_sum = 0
        main_chain_arrival_count = 0
        finalization_sum = 0
        finalization_count = 0
        for row in reader:
            if row['pool block arrival timestamp']!='None':
                pool_block_arr_sum += float(row['pool block arrival timestamp']) - float(row['generated timestamp'])
                pool_block_arr_count += 1
            if row['pool block reference timestamp']!='None' and row['pool block arrival timestamp']!='None':
                pool_block_ref_sum += float(row['pool block reference timestamp']) - float(row['pool block arrival timestamp'])
                pool_block_ref_count += 1
            if row['main chain arrival timestamp']!='None' and row['pool block arrival timestamp']!='None':
                main_chain_arrival_sum += float(row['main chain arrival timestamp']) - float(row['pool block arrival timestamp'])
                main_chain_arrival_count += 1
            if row['finalization timestamps']!='None':
                max_finalization_timestamp = max(list(map(lambda t: float(t),
                    row['finalization timestamps'].split(';')))) 
                finalization_sum += max_finalization_timestamp - float(row['main chain arrival timestamp'])
                finalization_count += 1

    avg_pool_block_arr_latency = 0 if pool_block_arr_count==0 else pool_block_arr_sum/pool_block_arr_count
    avg_pool_block_ref_latency = 0 if pool_block_ref_count==0 else pool_block_ref_sum/pool_block_ref_count
    avg_main_chain_arrival_latency = 0 if main_chain_arrival_count==0 else main_chain_arrival_sum/main_chain_arrival_count
    avg_finalization_latency = 0 if finalization_count==0 else finalization_sum/finalization_count
    return avg_pool_block_arr_latency, avg_pool_block_ref_latency, avg_main_chain_arrival_latency, avg_finalization_latency

def dump_results(foldername='logs'):
    print('Results:')
    avg_pool_block_arr_latency, avg_pool_block_ref_latency, avg_main_chain_arrival_latency, avg_finalization_latency = compute_latency(foldername) 
    transaction_throughput, unique_transaction_throughput = compute_throughputs(foldername)
    emptiness = compute_emptiness(foldername)
    print(f'Transaction Throughput: {transaction_throughput} transactions/sec')
    print(f'Unique Transaction Throughput: {unique_transaction_throughput} transactions/sec')
    print(f'Emptiness: {emptiness} txs')
    print(f'Pool Block Arrival Latency: {avg_pool_block_arr_latency} sec/transaction')
    print(f'Pool Block Reference Latency: {avg_pool_block_ref_latency} sec/transaction')
    print(f'Main Chain Arrival Latency: {avg_main_chain_arrival_latency} sec/transaction')
    print(f'Finalization Latency: {avg_finalization_latency} sec/transaction')

if __name__=='__main__':
    if len(sys.argv)>1:
        foldername = sys.argv[1]
    else:
        foldername = 'logs'
    dump_params()
    dump_results(foldername)
