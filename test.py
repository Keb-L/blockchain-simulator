import unittest
from algorithms import *
from block import *

class TestBlockchainSimulator(unittest.TestCase):
    def test_longest_chain(self):
        l = LongestChain()

        # create our own tree 
        block_a = Block(id='a', parent_id='Genesis')
        l.add_block_by_parent(parent_block=l.vertex_to_blocks[l.root], new_block=block_a) 

        block_b = Block(id='b', parent_id='Genesis')
        l.add_block_by_parent(parent_block=block_a, new_block=block_b) 

        block_c = Block(id='c', parent_id='b')
        l.add_block_by_parent(parent_block=block_b, new_block=block_c) 

        block_d = Block(id='d', parent_id='b')
        l.add_block_by_parent(parent_block=block_b, new_block=block_d) 

        parent_blocks = l.fork_choice_rule()

        self.assertIn(block_c, parent_blocks)
        self.assertIn(block_d, parent_blocks)

        chains = l.main_chains()

        block_chain_1 = list(map(lambda block: block.id,
                chains[0]))
        block_chain_2 = list(map(lambda block: block.id,
                chains[1]))


        self.assertListEqual(block_chain_1, ['Genesis', block_b.id, block_c.id]) 
        self.assertListEqual(block_chain_2, ['Genesis', block_b.id, block_d.id]) 

    def test_GHOST(self):
        g = GHOST()

        # create our own tree 
        block_a = Block(id='a', parent_id='Genesis')
        g.add_block_by_parent(parent_block=g.vertex_to_blocks[g.root], new_block=block_a) 

        block_b = Block(id='b', parent_id='Genesis')
        g.add_block_by_parent(parent_block=g.vertex_to_blocks[g.root], new_block=block_b) 

        block_c = Block(id='c', parent_id='b')
        g.add_block_by_parent(parent_block=block_b, new_block=block_c) 

        block_d= Block(id='d', parent_id='b')
        g.add_block_by_parent(parent_block=block_b, new_block=block_d) 

        parent_blocks = g.fork_choice_rule()

        self.assertIn(block_c, parent_blocks)
        self.assertIn(block_d, parent_blocks)

        chains = g.main_chains()

        block_chain_1 = list(map(lambda block: block.id,
                chains[0]))
        block_chain_2 = list(map(lambda block: block.id,
                chains[1]))

        self.assertListEqual(block_chain_1, ['Genesis', block_b.id, block_c.id]) 
        self.assertListEqual(block_chain_2, ['Genesis', block_b.id,block_d.id]) 

    def test_common_prefix(self):
        g = GHOST()

        # create our own tree 
        block_a = Block(id='a', parent_id='Genesis')
        g.add_block_by_parent(parent_block=g.vertex_to_blocks[g.root], new_block=block_a) 

        block_b = Block(id='b', parent_id='Genesis')
        g.add_block_by_parent(parent_block=g.vertex_to_blocks[g.root], new_block=block_b) 

        block_c = Block(id='c', parent_id='b')
        g.add_block_by_parent(parent_block=block_b, new_block=block_c) 

        block_d= Block(id='d', parent_id='b')
        g.add_block_by_parent(parent_block=block_b, new_block=block_d) 

        common_prefix = list(map(lambda block: block.id,
            g.common_prefix()))

        self.assertListEqual(common_prefix, ['Genesis', block_b.id])

    def test_longest_chain_with_pool(self):
        l = LongestChainWithPool()
        # create our own tree 
        block_a= LinkedBlock(id='a', parent_id='Genesis', block_type='tree')
        l.add_block_by_parent(parent_block=l.vertex_to_blocks[l.root], new_block=block_a) 

        # create two pool blocks
        block_1 = LinkedBlock(id='1', block_type='pool')
        block_2 = LinkedBlock(id='2', block_type='pool')

        l.add_pool_block(block_1)
        l.add_pool_block(block_2)

        block_b = LinkedBlock(id='b', block_type='tree')
        l.add_block_by_fork_choice_rule(block_b)

        chains = l.main_chains()

        block_chain_1 = list(map(lambda block: block.id,
                chains[0]))

        # block b should refer to block 1 and block 2
        self.assertListEqual(block_chain_1, ['Genesis', block_a.id, block_1.id,
            block_2.id, block_b.id])

    def test_prism(self):
        p = Prism(num_voting_chains = 2)
        # create our own tree 
        block_a = PrismBlock(id='a', parent_id='Genesis', block_type='proposer')
        p.add_block_by_parent(parent_block=p.vertex_to_blocks[p.root], new_block=block_a) 

        # add some blocks to block tree 1
        block_a_1 = PrismBlock(id = 'a1', parent_id='Genesis', block_type='voter')
        block_a_1.block_chain = 0
        p.add_block_by_fork_choice_rule(block_a_1)
        block_b_1 = PrismBlock(id = 'b1', parent_id='a1', block_type='voter')
        block_b_1.block_chain = 0
        p.add_block_by_fork_choice_rule(block_b_1)

        # add some blocks to block tree 2
        block_a_2 = PrismBlock(id = 'a2', parent_id='Genesis', block_type='voter')
        block_a_2.block_chain = 1
        p.add_block_by_fork_choice_rule(block_a_2)
        block_b_2 = PrismBlock(id = 'b2', parent_id='a2', block_type='voter')
        block_b_2.block_chain = 1
        p.add_block_by_fork_choice_rule(block_b_2)

        block_chain = list(map(lambda b: b.id, p.main_chains()[0]))
        # a1 and a2 should vote for block a
        # b1 and b2 should be absent since a1 and a2 have already voted for a
        self.assertListEqual(block_chain, ['Genesis', block_a_1.id, block_a_2.id, block_a.id]) 

        # add one more block to proposer tree
        block_b = PrismBlock(id='b', parent_id='a', block_type='proposer')
        p.add_block_by_parent(parent_block=block_a, new_block=block_b) 

        # add more blocks to block tree 1
        block_c_1 = PrismBlock(id = 'c1', parent_id='b1', block_type='voter')
        block_c_1.block_chain = 0
        p.add_block_by_fork_choice_rule(block_c_1)

        block_chain = list(map(lambda b: b.id, p.main_chains()[0]))
        # now c1 should have voted on block b and be added to main chain
        self.assertListEqual(block_chain, ['Genesis', block_a_1.id, block_a_2.id, block_a.id, block_c_1.id, block_b.id])

    def test_OHIE(self):
        o = OHIE(num_longest_chains=2)
        block_a = Block(id='a')
        o.add_block_to_chain(block_a, 0)
        self.assertEqual(1, block_a.depth)
        self.assertEqual(2, block_a.next_depth)

        block_b = Block(id='b')
        o.add_block_to_chain(block_b, 0)
        self.assertEqual(2, block_b.depth)
        self.assertEqual(3, block_b.next_depth)

        block_c = Block(id='c')
        o.add_block_to_chain(block_c, 1)
        self.assertEqual(1, block_c.depth)
        self.assertEqual(3, block_c.next_depth)

        block_d = Block(id='d')
        o.add_block_to_chain(block_d, 1)
        self.assertEqual(3, block_d.depth)
        self.assertEqual(4, block_d.next_depth)

        chains = o.main_chains()
        block_chain_0 = list(map(lambda block: block.id, chains[0][0]))
        self.assertListEqual(block_chain_0, ['Genesis0', 'a', 'b'])
        block_chain_1 = list(map(lambda block: block.id, chains[1][0]))
        self.assertListEqual(block_chain_1, ['Genesis1', 'c', 'd'])

if __name__ == '__main__':
    unittest.main()
