import sys, re, json, pprint, csv, glob
from constants import TX_RATE

def dump_params(filename='params.json'):
    print('Parameters:')
    with open(f'{filename}') as f:
        contents = json.load(f)
        setting_name = contents['setting-name']
        d = contents[setting_name]
    
    pp = pprint.PrettyPrinter()
    pp.pprint(d)
    print('\n')

def compute_throughputs(foldername='logs', filename='params.json'):
    with open(f'{filename}') as f:
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
                else:
                    num_transactions_finalized+=1

    return float(num_transactions_finalized)/duration, float(num_unique_transactions_finalized)/duration

def compute_latency(foldername='logs'):
    with open(f'{foldername}/transactions.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        main_chain_arrival_sum = 0
        main_chain_arrival_count = 0
        finalization_sum = 0
        finalization_count = 0
        for row in reader:
            if row['main chain arrival timestamp']!='None' and row['generated timestamp']!='None':
                main_chain_arrival_sum += float(row['main chain arrival timestamp']) - float(row['generated timestamp'])
                main_chain_arrival_count += 1
            if row['finalization timestamps']!='None':
                max_finalization_timestamp = min(list(map(lambda t: float(t),
                    row['finalization timestamps'].split(';')))) 
                finalization_sum += max_finalization_timestamp - float(row['main chain arrival timestamp'])
                finalization_count += 1

    avg_main_chain_arrival_latency = 0 if main_chain_arrival_count==0 else main_chain_arrival_sum/main_chain_arrival_count
    avg_finalization_latency = 0 if finalization_count==0 else finalization_sum/finalization_count
    return avg_main_chain_arrival_latency, avg_finalization_latency

def dump_results(foldername='logs'):
    print('Results:')
    avg_main_chain_arrival_latency, avg_finalization_latency = compute_latency(foldername) 
    transaction_throughput, unique_transaction_throughput = compute_throughputs(foldername)
    print(f'Transaction Throughput: {transaction_throughput} transactions/sec')
    print(f'Unique Transaction Throughput: {unique_transaction_throughput} transactions/sec')
    print(f'Main Chain Arrival Latency: {avg_main_chain_arrival_latency} sec/transaction')
    print(f'Finalization Latency: {avg_finalization_latency} sec/transaction')

if __name__=='__main__':
    if len(sys.argv)>1:
        foldername = sys.argv[1]
    else:
        foldername = 'logs'
    dump_params()
    dump_results(foldername)
