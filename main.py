import sys, os, shutil, json, numpy as np
from optparse import OptionParser
from coordinator import Coordinator
from node import Node
import generate_tx_dataset

def get_params(filename):
    params = {}
    with open(f'{filename}') as f:
        contents = json.load(f)
        setting_name = contents['setting-name']
        d = contents[setting_name]
        params['num_nodes'] = d['Number of nodes'] 
        params['max_block_size'] = d['Block size (txs)']
        params['tx_error_prob'] = d['Probability of error in transaction confirmation']
        params['proposal_rate'] = d['Block proposal rate parameter']
        params['dataset'] = d['Transaction dataset']
        params['model'] = d['Network model']
        params['fork_choice_rule'] = d['Fork choice rule']
        params['duration'] = d['Duration (sec)']
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
    # generate num_nodes nodes
    for node_id in range(0, params['num_nodes']): 
        n = Node(node_id, params['fork_choice_rule'])
        nodes[node_id] = n
        c.add_node(n)
    
    # every node is a neighbor of the other for right now
    for i in range (0, len(nodes)): 
        for j in range(0, len(nodes)):
            if i!=j:
                nodes[i].add_neighbor(nodes[j])
    
    # generate mock poisson dataset
    if params['dataset']=='poisson':
        tx_dataset = generate_tx_dataset.poisson(0.1, params['duration'], c.clock, c.nodes)
    elif params['dataset']=='deterministic':
        tx_dataset = generate_tx_dataset.deterministic(0.1, params['duration'], c.clock, c.nodes)

    # generate proposal events
    c.generate_proposals()
    # set transaction dataset
    c.set_transactions(tx_dataset)

    # run simulation
    c.run()
