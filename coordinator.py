import random, csv, os, numpy as np, time
import logger
from node import Node
from events import Proposal
from algorithms import *
from tqdm import tqdm

class Coordinator():
    def __init__(self, params):
        self.proposals = np.array([])
        self.nodes = np.array([])
        self.txs = np.array([])

        self.params = params

        self.leader = None

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

        elif self.params['fork_choice_rule']=='BitcoinNG' and self.params['microblock_proposal_rate']>0:
            proposals = []

            # Generate timestamp for the first block
            timestamp = np.random.exponential(1.0/self.params['tree_proposal_rate'])
            while timestamp<self.params['duration']: 
                # Generate and append key block
                proposal = Proposal(timestamp, proposal_type='key') 
                proposals.append(proposal)

                # Compute arrival time of next keyblock
                next_arrival = np.random.exponential(1.0/self.params['tree_proposal_rate'])
                micro_timestamp = self.params['microblock_proposal_rate']

                # Generate microblocks 
                while (micro_timestamp + self.params['microblock_proposal_rate']) < min(next_arrival, self.params['duration']):
                    if timestamp + micro_timestamp > self.params['duration']:
                        break
                    proposal = Proposal(timestamp + micro_timestamp, proposal_type='micro') 
                    proposals.append(proposal)

                    # Compute the next micro timestamp
                    micro_timestamp = micro_timestamp + self.params['microblock_proposal_rate']


                # End microblock loop
                timestamp = timestamp + next_arrival
            # End keyblock loop        
            
            # Last Proposal     
            del proposals[-1]
            last_proposal = Proposal(self.params['duration'], proposal_type='key')
            proposals.append(last_proposal)
        # End bitcoinNG proposal generation

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
                
                # if finalized_block.block_type is 'key':
                #     finalized_block.get_tx()

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
                
                if hasattr(finalized_block, 'micro_blocks'):
                    # referenced blocks have a finalization timestamp and
                    # proposal timestamp equal
                    # to the finalized block on the main chain
                    for micro_block in finalized_block.micro_blocks:
                        micro_block.set_finalization_timestamp(finalized_block.finalization_timestamp)

                        for tx in micro_block.txs:
                            tx.set_main_chain_arrival_timestamp(micro_block.proposal_timestamp)
                            tx.set_complete()
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
            elif self.params['fork_choice_rule'] =='BitcoinNG':
                main_chain = list(filter(lambda block:
                block.block_type!='micro', main_chain))
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

    def finalize_proposals(self, common_blocks):
        # For each proposal
        common_blocks_ids = [x.id for x in common_blocks]

        for i in range(0, len(self.proposals)):
            prop = self.proposals[i]

            # Get its block
            block = prop.block
            block_id = block.id

            if block.block_type is 'micro':
                block_id = block.parent_id

            # Find corresponding block in common blocks
            if block_id in common_blocks_ids:
                self.proposals[i].block.finalization_timestamp = common_blocks[common_blocks_ids.index(block_id)].finalization_timestamp




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
        pbar = tqdm(total=self.txs.shape[0]+self.proposals.shape[0])

        # run main loop
        while tx_i<self.txs.shape[0] or p_i<self.proposals.shape[0]:
            # Print the current progress
            # if (tx_i+p_i)%100==0:
                # print(float(tx_i+p_i)/(self.txs.shape[0]+self.proposals.shape[0]))

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
                    pbar.update(1)
                # proposal before transaction
                else:
                    # choose proposer uniformly at random (for key proposals)
                    # Otherwise, for microblocks, use the leader
                    proposal_type = self.proposals[p_i].proposal_type
                    if proposal_type != 'micro': # If not a micro proposal, randomize the leader
                        self.leader = random.choice(self.nodes)

                    proposer = self.leader
                    proposal = proposer.propose(self.proposals[p_i],
                        self.params['max_block_size'],
                        self.params['fork_choice_rule'],
                        self.params['model'])
                    # broadcast to rest of network
                    proposer.broadcast(proposal, self.params['max_block_size'],
                            self.params['model'])
                    p_i+=1
                    pbar.update(1)
            # out of all proposals
            elif p_i==self.proposals.shape[0]:
                tx = self.txs[tx_i]
                source_node = tx.source
                source_node.broadcast(tx, self.params['max_block_size'],
                        self.params['model'])
                tx_i+=1
                pbar.update(1)
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
                pbar.update(1)

        pbar.close()

        for node in self.nodes:
            node.process_buffer(self.params['duration'])

        common_blocks = self.global_main_chain() 
        self.set_timestamps(common_blocks)

        # Finalize proposals
        self.finalize_proposals(common_blocks)

        end = time.time()

        print("Complete! Logging results")

        if self.params['logging']:
            logger.log_txs(self.params, self.txs)
            logger.log_blocks(self.params, self.proposals)
            logger.log_statistics(self.params, common_blocks, self.proposals, self.txs, end-start)
            # logger.draw_blocktree(self.params, self.proposals, common_blocks)

            # os.system('cat ./logs/stats.csv')
