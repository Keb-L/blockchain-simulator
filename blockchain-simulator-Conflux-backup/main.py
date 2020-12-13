import sys, os, shutil, json, numpy as np
from optparse import OptionParser
from topology_reader import get_topology
from coordinator import Coordinator
from node import Node
from constants import TX_RATE
import generate_tx_dataset

def get_params(filename):
    params = {}
    with open(filename) as f:
        contents = json.load(f)
        setting_name = contents['setting-name']
        d = contents[setting_name]
        params['num_nodes'] = d['Number of nodes'] 
        params['num_adversaries'] = d['Number of adversaries']
        params['max_block_size'] = d['Block size (txs)']
        params['tx_error_prob'] = d['Probability of error in transaction confirmation']
        params['fork_choice_rule'] = d['Fork choice rule']
        # if the fork choice rule is longest chain with pool, we should have 2
        # proposal rates f_t for the tree and f_p for the pool
        if d['Fork choice rule']=='longest-chain-with-pool':
            params['tree_proposal_rate'] = d['Block tree proposal rate parameter']
            params['pool_proposal_rate'] = d['Block pool proposal rate parameter']
        else:
            params['tree_proposal_rate'] = d['Block proposal rate parameter']
        if 'Transaction rate parameter' in d:
            params['transaction_rate'] = d['Transaction rate parameter']
        params['transaction_schedule'] = d['Transaction scheduling rule']
        params['dataset'] = d['Transaction dataset']
        params['model'] = d['Network model']
        params['duration'] = d['Duration (sec)']
        params['logging'] = d['Logging enabled']
        if 'Topology file' in d:
            params['topology'] = d['Topology file']
        if 'Locations file' in d:
            params['locations'] = d['Locations file']
    return params

if __name__=='__main__':
    usage = 'usage: python %prog [options]'
    parser = OptionParser(usage=usage)

    parser.add_option('-f', '--filename', type='string',
            action='store', dest='filename', default='params.json',
            help='filename to set parameters; default parameters are in params.json')

    (options, args) = parser.parse_args(sys.argv[1:])

    params = get_params(options.filename)

    # Setup logging directory 
    shutil.rmtree('./logs')
    os.mkdir('./logs')

    c = Coordinator(params) 
    nodes = np.empty(params['num_nodes'], dtype=Node)

    if 'topology' in params and 'locations' in params:
        num_nodes, locations, G = get_topology(params['locations'],
        params['topology'])
        if num_nodes!=params['num_nodes']:
            print('Invalid number of nodes provided')
            sys.exit()
        # generate num_nodes nodes
        for node_id in range(0, num_nodes): 
            n = Node(node_id, params['fork_choice_rule'],
                    params['transaction_schedule'], params['max_block_size'], locations[node_id])
            nodes[node_id] = n
            c.add_node(n)

        # add nodes to network based on graph topology
        for node_id in range(0, num_nodes):
            for neighbor in G[node_id]:
                n.add_neighbor(nodes[neighbor])
    else:
        # generate num_nodes nodes
        num_nodes = params['num_nodes']
        for node_id in range(0, num_nodes):   
            n = Node(node_id, params['fork_choice_rule'],
                    params['transaction_schedule'],
                    params['max_block_size'])
            nodes[node_id] = n    ##### id 与 Node Class对应 main中nodes是dict
            c.add_node(n)
        
        # every node is a neighbor of the other for right now
        for i in range (0, len(nodes)): 
            for j in range(0, len(nodes)):
                if i!=j:
                    nodes[i].add_neighbor(nodes[j])
    
    tx_rate = TX_RATE if 'transaction_rate' not in params else params['transaction_rate']
    
    if params['dataset']=='poisson':
        tx_dataset = generate_tx_dataset.poisson(tx_rate, params['duration'], 0, c.nodes)
    elif params['dataset']=='deterministic':
        tx_dataset = generate_tx_dataset.deterministic(tx_rate,
                params['duration'], 0, c.nodes)


    # generate proposal events
    c.generate_proposals()
    # set transaction dataset
    c.set_transactions(tx_dataset)

    # create arrays to store proposals and transactions
    for node_id in range(0, num_nodes): 
        nodes[node_id].create_arrays(len(tx_dataset)) 


    # run simulation
    c.run()

