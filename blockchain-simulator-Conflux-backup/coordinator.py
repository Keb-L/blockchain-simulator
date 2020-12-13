import random, csv, os, numpy as np, time
import logger
from node import Node
from events import Proposal
from algorithms import *

class Coordinator():
    def __init__(self, params):
        self.proposals = np.array([])    
        self.nodes = np.array([])   
        self.txs = np.array([])

        self.params = params     

    def add_node(self, node):
        self.nodes = np.append(self.nodes, node)

    def generate_proposals(self):
        timestamp = 0

        proposals = []

        # generate tree proposal events
        while timestamp<self.params['duration']: 
            timestamp = timestamp + np.random.exponential(1.0/self.params['tree_proposal_rate'])
            proposal = Proposal(timestamp, proposal_type='tree') 
            proposals.append(proposal)

        del proposals[-1]
        last_proposal = Proposal(self.params['duration'], proposal_type='tree')
        proposals.append(last_proposal)


        if self.params['fork_choice_rule']=='longest-chain-with-pool' and self.params['pool_proposal_rate']>0:
            timestamp = 0
            # generate pool proposal events
            while timestamp<self.params['duration']: 
                timestamp = timestamp + np.random.exponential(1.0/self.params['pool_proposal_rate'])
                proposal = Proposal(timestamp, proposal_type='pool') 
                proposals.append(proposal)
        
        '''
        elif self.params['fork_choice_rule']=='Conflux':
            timestamp = 0
            # generate pool proposal events
            while timestamp<self.params['duration']:
                timestamp = timestamp + np.random.exponential(1.0/self.params['pool_proposal_rate'])
                proposal = Proposal(timestamp, proposal_type='tree')
                proposals.append(proposal)
        '''
        
        self.proposals = np.asarray(sorted(proposals, key = lambda
            proposal: proposal.timestamp))

    def set_transactions(self, dataset):
        self.txs = np.asarray(dataset)

    def set_timestamps(self, global_main_chain):
        finalization_depth = compute_finalization_depth(self.params['tx_error_prob'],
                self.params['num_nodes'], self.params['num_adversaries'])

        # For each common block
        # iterate through all transactions and set to complete and add
        # finalization, main chain arrival timestamps
        for common_block in global_main_chain:
            # finalized blocks are finalization depth above common block
            finalized_blocks = filter(lambda block:
                 block.depth<=common_block.depth-finalization_depth,
                global_main_chain)
            for finalized_block in finalized_blocks:
                finalized_block.set_finalization_timestamp(common_block.proposal_timestamp)
                for tx in finalized_block.txs:
                    # transaction arrives to main chain when finalized block
                    # is proposed
                    tx.set_main_chain_arrival_timestamp(finalized_block.proposal_timestamp)
                    # transaction is finalized when common block is proposed
                    tx.set_complete()
                    tx.add_finalization_timestamp(common_block.proposal_timestamp)
                if hasattr(finalized_block, 'referenced_blocks'):
                    # referenced blocks have a finalization timestamp and
                    # proposal timestamp equal
                    # to the finalized block on the main chain
                    for ref_block in finalized_block.referenced_blocks:
                        ref_block.set_finalization_timestamp(finalized_block.finalization_timestamp)
                        for tx in ref_block.txs:
                            tx.set_main_chain_arrival_timestamp(finalized_block.proposal_timestamp)
                            tx.add_finalization_timestamp(finalized_block.finalization_timestamp)


    def global_main_chain(self):
        main_chains = []
        main_chain_ids = []

        # Get block ids in all main chains
        for node in self.nodes:
            main_chain = node.local_blocktree.random_main_chain()
            # Prism has unique protocol 
            # exclusively add non voter blocks
            if self.params['fork_choice_rule']=='Prism':
                main_chain = list(filter(lambda block:
                block.block_type!='voter', main_chain))
            main_chains.append(main_chain)
            main_chain_ids.append(list(map(lambda block: block.id,
                main_chains[-1])))

        # Find blocks common to all main chains
        common_block_ids = set(main_chain_ids[0])
        for blocks in main_chain_ids[1:]:
            common_block_ids.intersection_update(blocks)

        common_blocks = []
        for common_block_id in common_block_ids:
            common_block = next(filter(lambda block: block.id==common_block_id,
                    main_chains[0]))
            common_blocks.append(common_block)

        # In Prism, once we have common proposer blocks, add ALL referenced
        # blocks
        if self.params['fork_choice_rule']=='Prism':
            updated_common_blocks = []
            for common_block in common_blocks:
                for node in self.nodes:
                    referenced_blocks = node.local_blocktree.get_referenced_blocks(common_block.id)
                    updated_common_blocks+=list(referenced_blocks)
                updated_common_blocks+=[common_block]
            common_blocks = updated_common_blocks

        return common_blocks 

    def global_block_order(self):

        common_blocks_order = self.nodes[0].local_block_order
        for node in self.nodes:
            common_blocks_order = [i for i in common_blocks_order if i in node.local_block_order]
        blocks_order_nodes = []
        for node in self.nodes:
            #blocks_order_node_i
            blocks_order_nodes.append([i for i in node.local_block_order if i in common_blocks_order])
        #for i, block in enumerate(common_blocks_order):
        #    for blocks_order_node_i in blocks_order_nodes:
        
        return common_blocks_order

 
    def node_pivot_chain(self):
        pivot_chains = []
        pivot_chain_ids = []

        # Get block ids in all main chains
        for node in self.nodes:
            pivot_chain = node.local_blocktree.random_pivot_chain()
            pivot_chains.append(pivot_chain)
            pivot_chain_ids.append(list(map(lambda block: block.id,
                pivot_chains[-1])))




    '''
    Main simulation function
    Coordinator checks head of proposal and tx queue and processes earlier
    occurring event
        - Coordinator moves global clock to next event timestamp
        - If event is a proposal
            - Choose a node uniformly at random
            - Chosen node calls propose()
        - If event is a tx
            - Broadcast tx from source node
        - After main loop, loop over all all nodes and process buffer
    '''
    def run(self):
        start = time.time()

        tx_i = 0
        p_i = 0

        while tx_i<self.txs.shape[0] or p_i<self.proposals.shape[0]:
            if (tx_i+p_i)%100==0:
                print(float(tx_i+p_i)/(self.txs.shape[0]+self.proposals.shape[0]))
            # still have valid txs and proposals
            if tx_i<self.txs.shape[0] and p_i<self.proposals.shape[0]:
                # transaction before proposal
                if self.txs[tx_i].timestamp < self.proposals[p_i].timestamp:
                    # transaction processing occurs when a node is selected to
                    # be a proposer, so don't do anything but increment
                    # transaction index and move global clock
                    tx = self.txs[tx_i]
                    source_node = tx.source

                    source_node.local_txs[source_node.local_tx_i] = tx
                    source_node.local_tx_i+=1

                    source_node.broadcast(tx, self.params['max_block_size'],
                            self.params['model'])
                    tx_i+=1
                # proposal before transaction
                else:
                    # choose proposer uniformly at random
                    proposer = random.choice(self.nodes)   ## Node Class
                    proposal = proposer.propose(self.proposals[p_i],   
                        self.params['max_block_size'],
                        self.params['fork_choice_rule'],
                        self.params['model'])
                    # broadcast to rest of network
                    proposer.broadcast(proposal, self.params['max_block_size'],
                            self.params['model'])
                    p_i+=1
            # out of all proposals
            elif p_i==self.proposals.shape[0]:
                tx = self.txs[tx_i]
                source_node = tx.source
                source_node.broadcast(tx, self.params['max_block_size'],
                        self.params['model'])
                tx_i+=1
            # out of all transactions
            elif tx_i==self.txs.shape[0]:
                # choose proposer uniformly at random
                proposer = random.choice(self.nodes)
                proposal = proposer.propose(self.proposals[p_i], 
                    self.params['max_block_size'],
                    self.params['fork_choice_rule'],
                    self.params['model'])
                # broadcast to rest of network
                proposer.broadcast(proposal, self.params['max_block_size'],
                        self.params['model'])
                p_i+=1

        for node in self.nodes:
            node.process_buffer(self.params['duration'])
            if node.algorithms == 'Conflux':

                node.local_pivot_chain = node.local_blocktree.random_pivot_chain()
                node.local_epochs, node.local_block_order = node.local_blocktree.topology_sorting(
                    node.local_pivot_chain)
                conflux = True

        if conflux:
            common_blocks = self.global_block_order() 
        else:
            common_blocks = self.global_main_chain()

        self.set_timestamps(common_blocks)

        end = time.time()
        if self.params['logging']:
            logger.log_txs(self.txs)
            logger.log_blocks(self.params, self.proposals)
            logger.log_statistics(self.params, common_blocks, self.proposals, end-start)
            logger.draw_blocktree(self.params, self.proposals, common_blocks)

            os.system('cat ./logs/stats.csv')
