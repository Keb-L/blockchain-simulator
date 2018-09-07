import re, json, pprint, csv
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
    return main_chain_arrival_sum/main_chain_arrival_count, finalization_sum/finalization_count

def dump_results():
    print('Results:')
    avg_main_chain_arrival_latency, avg_finalization_latency = compute_latency() 
    print(f'Transaction Throughput: {compute_throughput()} transactions/sec')
    print(f'Main Chain Arrival Latency: {avg_main_chain_arrival_latency} sec/transaction')
    print(f'Finalization Latency: {avg_finalization_latency} sec/transaction')

if __name__=='__main__':
    dump_params()
    dump_results()
