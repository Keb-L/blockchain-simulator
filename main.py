import sys, os, shutil, json
from optparse import OptionParser
from coordinator import Coordinator
from node import Node
import generate_dataset

def get_params(filename):
    params = {}
    with open(f'{filename}') as f:
        d = json.load(f)
        params['num_nodes'] = d['Number of nodes'] 
        params['max_block_size'] = d['Block size (txs)']
        params['tx_error_prob'] = d['Probability of error in transaction confirmation']
        params['proposal_rate'] = d['Block proposal rate parameter']
        params['dataset'] = d['Transaction dataset']
        params['model'] = d['Network model']
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

    c = Coordinator() 
    nodes = []
    # generate num_nodes nodes
    for node_id in range(0, params['num_nodes']): 
        n = Node(node_id)
        nodes.append(n)
        c.add_node(n)
    
    # every node is a neighbor of the other for right now
    for i in range (0, len(nodes)): 
        for j in range(0, len(nodes)):
            if i!=j:
                nodes[i].add_neighbor(nodes[j])
    
    # generate mock poisson and deterministic dataset
    poisson_dataset = generate_dataset.poisson(0.1, params['duration'], c.clock, c.nodes)
    deterministic_dataset = generate_dataset.deterministic(0.1, params['duration'], c.clock, c.nodes)

    # generate proposal events
    c.generate_proposals(params['proposal_rate'], params['duration'])
    # set transaction dataset
    c.set_transactions(deterministic_dataset)

    # run simulation
    c.run(params['max_block_size'])
