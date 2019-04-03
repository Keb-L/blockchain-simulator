import unittest
from algorithms import *
from block import Block

class TestBlockchainSimulator(unittest.TestCase):
    def test_longest_chain(self):
        l = LongestChain()

        # create our own tree 
        a_block = Block(id='a', parent_id='Genesis')
        l.add_block_by_parent_id(a_block) 

        b_block = Block(id='b', parent_id='Genesis')
        l.add_block_by_parent_id(b_block) 

        c_block = Block(id='c', parent_id='b')
        l.add_block_by_parent_id(c_block) 

        d_block = Block(id='d', parent_id='b')
        l.add_block_by_parent_id(d_block) 

        parent_blocks = l.fork_choice_rule()

        self.assertIn(c_block, parent_blocks)
        self.assertIn(d_block, parent_blocks)

        chains = l.main_chains()

        block_chain_1 = list(map(lambda block: block.id,
                chains[0]))
        block_chain_2 = list(map(lambda block: block.id,
                chains[1]))

        self.assertListEqual(block_chain_1, ['Genesis', b_block.id, c_block.id]) 
        self.assertListEqual(block_chain_2, ['Genesis', b_block.id, d_block.id]) 

    def test_GHOST(self):
        g = GHOST()

        # create our own tree 
        a_block = Block(id='a', parent_id='Genesis')
        g.add_block_by_parent_id(a_block) 

        b_block = Block(id='b', parent_id='Genesis')
        g.add_block_by_parent_id(b_block) 

        c_block = Block(id='c', parent_id='b')
        g.add_block_by_parent_id(c_block) 

        d_block = Block(id='d', parent_id='b')
        g.add_block_by_parent_id(d_block) 

        parent_blocks = g.fork_choice_rule()

        self.assertIn(c_block, parent_blocks)
        self.assertIn(d_block, parent_blocks)

        chains = g.main_chains()

        block_chain_1 = list(map(lambda block: block.id,
                chains[0]))
        block_chain_2 = list(map(lambda block: block.id,
                chains[1]))

        self.assertListEqual(block_chain_1, ['Genesis', b_block.id, c_block.id]) 
        self.assertListEqual(block_chain_2, ['Genesis', b_block.id, d_block.id]) 

    def test_common_prefix(self):
        g = GHOST()

        # create our own tree 
        a_block = Block(id='a', parent_id='Genesis')
        g.add_block_by_parent_id(a_block) 

        b_block = Block(id='b', parent_id='Genesis')
        g.add_block_by_parent_id(b_block) 

        c_block = Block(id='c', parent_id='b')
        g.add_block_by_parent_id(c_block) 

        d_block = Block(id='d', parent_id='b')
        g.add_block_by_parent_id(d_block) 

        common_prefix = list(map(lambda block: block.id,
            g.common_prefix()))

        self.assertListEqual(common_prefix, ['Genesis', b_block.id])

    def test_longest_chain_with_pool(self):
        l = LongestChainWithPool()
        # create our own tree 
        block_a = Block(id='a', parent_id='Genesis', block_type='tree')
        l.add_block_by_parent_id(block_a) 

        # create two pool blocks
        block_1 = Block(id='1', block_type='pool')
        block_2 = Block(id='2', block_type='pool')

        l.add_pool_block(block_1)
        l.add_pool_block(block_2)

        block_b = Block(id='b', block_type='tree')
        l.add_block_by_fork_choice_rule(block_b)

        chains = l.main_chains()

        block_chain_1 = list(map(lambda block: block.id,
                chains[0]))

        self.assertListEqual(block_chain_1, ['Genesis', block_a.id, block_1.id,
            block_2.id, block_b.id])

    def test_prism(self):
        p = Prism(num_voting_chains = 2)
        # create our own tree 
        block_a = Block(id='a', parent_id='Genesis', block_type='proposer')
        p.add_block_by_parent_id(block_a) 

        # add some blocks to block tree 1
        block_a_1 = Block(id = 'a1', parent_id='Genesis', block_type='voter')
        block_a_1.block_chain = 0
        p.add_block_by_fork_choice_rule(block_a_1)
        block_b_1 = Block(id = 'b1', parent_id='a1', block_type='voter')
        block_b_1.block_chain = 0
        p.add_block_by_fork_choice_rule(block_b_1)

        # add some blocks to block tree 2
        block_a_2 = Block(id = 'a2', parent_id='Genesis', block_type='voter')
        block_a_2.block_chain = 1
        p.add_block_by_fork_choice_rule(block_a_2)
        block_b_2 = Block(id = 'b2', parent_id='a2', block_type='voter')
        block_b_2.block_chain = 1
        p.add_block_by_fork_choice_rule(block_b_2)

        block_chain = list(map(lambda b: b.id, p.main_chains()[0]))
        # a1 and a2 should vote for block a
        # b1 and b2 should be absent since a1 and a2 have already voted for a
        self.assertListEqual(block_chain, ['Genesis', block_a_1.id, block_a_2.id, block_a.id]) 

        # add one more block to proposer tree
        block_b = Block(id='b', parent_id='a', block_type='proposer')
        p.add_block_by_parent_id(block_b) 

        # add more blocks to block tree 1
        block_c_1 = Block(id = 'c1', parent_id='b1', block_type='voter')
        block_c_1.block_chain = 0
        p.add_block_by_fork_choice_rule(block_c_1)

        block_chain = list(map(lambda b: b.id, p.main_chains()[0]))
        # now c1 should have voted on block b and be added to main chain
        self.assertListEqual(block_chain, ['Genesis', block_a_1.id, block_a_2.id, block_a.id, block_c_1.id, block_b.id]) 
        
if __name__ == '__main__':
    unittest.main()
