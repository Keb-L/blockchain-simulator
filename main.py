import sys
from optparse import OptionParser
from coordinator import Coordinator
from node import Node
import generate_dataset

if __name__=='__main__':
    usage = 'usage: python %prog [options]'
    parser = OptionParser(usage=usage)

    parser.add_option('-n', '--num_nodes', type='int',
            action='store', dest='num_nodes', default=1,
            help='number of nodes in network; default is 1')

    parser.add_option('-b', '--block_size', type='int',
            action='store', dest='max_block_size', default=1,
            help='maximum number of transactions in a block; default is 1')

    parser.add_option('-e', '--epsilon', type='float',
            action='store', dest='epsilon', default=0.0,
            help='probability of error in transaction confirmation; default is 0.0')

    parser.add_option('-f', '--block_proposal_rate', type='float',
            action='store', dest='block_proposal_rate', default=1.0,
            help='rate of block proposals; default is 1.0')

    parser.add_option('-T', '--duration', type='int',
            action='store', dest='duration', default=60,
            help='duration of experiment is seconds; default is 60 seconds')


    (options, args) = parser.parse_args(sys.argv[1:])

    global_coordinator = Coordinator()

    # generate num_nodes nodes
    for node_id in range(0, options.num_nodes): 
        n = Node(node_id)
        global_coordinator.add_node(n)
    
    print(generate_dataset.poisson(0.1, 50, global_coordinator.nodes))
    print(generate_dataset.deterministic(0.1, 50, global_coordinator.nodes))
