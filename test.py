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

        block_chain_1 = list(map(lambda vertex: l.vertex_to_blocks[vertex].id,
                chains[0]))
        block_chain_2 = list(map(lambda vertex: l.vertex_to_blocks[vertex].id,
                chains[1]))

        self.assertListEqual(block_chain_1, [c_block.id, b_block.id, 'Genesis']) 
        self.assertListEqual(block_chain_2, [d_block.id, b_block.id, 'Genesis']) 

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

        self.assertListEqual(block_chain_1, [c_block.id, b_block.id, 'Genesis']) 
        self.assertListEqual(block_chain_2, [d_block.id, b_block.id, 'Genesis']) 


if __name__ == '__main__':
    unittest.main()
