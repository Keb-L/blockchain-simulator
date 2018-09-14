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

def compute_optimistic_confirmation_time():
    num_nodes = 0
    avg_optimistic_confirmation_sum = 0
    for filename in glob.glob('./logs/*-transactions.csv'):
        optimistic_confirmation_times = {}
        with open(f'{filename}', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            first_row = True
            for row in reader:
                if first_row:
                    first_row = False
                    continue
                else:
                    optimistic_confirmation_times[row['id']] = float(row['Optimistic confirmation timestamp'])
        with open(f'./logs/transactions.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            first_row = True
            for row in reader:
                if first_row:
                    first_row = False
                    continue
                else:
                    if row['id'] in optimistic_confirmation_times:
                        optimistic_confirmation_times[row['id']] -= float(row['Arrival Timestamp'])
        if len(optimistic_confirmation_times.keys())==0:
            avg_optimistic_confirmation_time = 0.0
        else:
            avg_optimistic_confirmation_time = sum(optimistic_confirmation_times.values())/len(optimistic_confirmation_times)
        avg_optimistic_confirmation_sum+=avg_optimistic_confirmation_time
        num_nodes+=1

    return float(avg_optimistic_confirmation_sum)/num_nodes

def compute_throughput():
    f = 0.95
    all_txs = []
    node_txs = []
    for filename in glob.glob('./logs/*.csv'):
        if filename.split('./logs/')[1].split('.csv')[0].isdigit():
            txs = []
            with open(filename, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    txs+=row['Transactions'].split(';')
            txs = list(filter(None,txs))
            all_txs +=txs
            node_txs.append(txs)
    
    tx_count=0
    for tx in all_txs:
        in_node_count = 0
        for txs in node_txs:
            if tx in txs:
                in_node_count+=1
        if float(in_node_count)/len(node_txs)>=f:
            tx_count+=1
    return TX_RATE

def compute_latency():
    with open('./logs/transactions.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        main_chain_arrival_sum = 0
        main_chain_arrival_count = 0
        finalization_sum = 0
        finalization_count = 0
        for row in reader:
            if row['Main Chain Arrival Timestamp']!='None':
                main_chain_arrival_sum += float(row['Main Chain Arrival Timestamp']) - float(row['Arrival Timestamp'])
                main_chain_arrival_count += 1
            if row['Finalization Timestamp']!='None':
                finalization_sum += float(row['Finalization Timestamp']) - float(row['Main Chain Arrival Timestamp'])
                finalization_count += 1

    avg_main_chain_arrival_latency = 0 if main_chain_arrival_count==0 else main_chain_arrival_sum/main_chain_arrival_count
    avg_finalization_latency = 0 if finalization_count==0 else finalization_sum/finalization_count
    return avg_main_chain_arrival_latency, avg_finalization_latency

def dump_results():
    print('Results:')
    avg_optimistic_confirmation_time = compute_optimistic_confirmation_time()
    avg_main_chain_arrival_latency, avg_finalization_latency = compute_latency() 
    print(f'Transaction Throughput: {compute_throughput()} transactions/sec')
    print(f'Optimistic Confirmation Time: {avg_optimistic_confirmation_time} sec')
    print(f'Main Chain Arrival Latency: {avg_main_chain_arrival_latency} sec/transaction')
    print(f'Finalization Latency: {avg_finalization_latency} sec/transaction')

if __name__=='__main__':
    dump_params()
    dump_results()
