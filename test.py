import unittest
from algorithms import *
from block import Block

class TestBlockchainSimulator(unittest.TestCase):
    '''
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

        block_chain_1 = list(map(lambda vertex: l.vertex_to_blocks[vertex].id,
                chains[0]))
        block_chain_2 = list(map(lambda vertex: l.vertex_to_blocks[vertex].id,
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

        block_chain_1 = list(map(lambda vertex: g.vertex_to_blocks[vertex].id,
                chains[0]))
        block_chain_2 = list(map(lambda vertex: g.vertex_to_blocks[vertex].id,
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

        common_prefix = list(map(lambda vertex: g.vertex_to_blocks[vertex].id,
            g.common_prefix()))

        self.assertListEqual(common_prefix, ['Genesis', b_block.id])
    '''

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

        block_chain_1 = list(map(lambda vertex: l.vertex_to_blocks[vertex].id,
                chains[0]))

        print(block_chain_1)


if __name__ == '__main__':
    unittest.main()
