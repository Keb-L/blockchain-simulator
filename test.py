import unittest
from algorithms import *
from block import Block

class TestBlockchainSimulator(unittest.TestCase):
    def test_longest_chain(self):
        l = LongestChain()
        # create our own tree 
        l.tree = Graph()
        l.root = l.tree.add_vertex()
        l.blocks[l.root] = Block()

        # add 2 blocks a and b as root's children
        a_block = Block()
        a_vertex = l.tree.add_vertex()
        l.blocks[a_vertex] = a_block
        l.tree.add_edge(l.root, a_vertex)

        b_block = Block()
        b_vertex = l.tree.add_vertex()
        l.blocks[b_vertex] = b_block
        l.tree.add_edge(l.root, b_vertex)

        # add 1 block c as a's child
        c_block = Block()
        c_vertex = l.tree.add_vertex()
        l.blocks[c_vertex] = c_block
        l.tree.add_edge(a_vertex, c_vertex)

        # add 2 blocks d and e as b's children
        d_block = Block()
        d_vertex = l.tree.add_vertex()
        l.blocks[d_vertex] = d_block
        l.tree.add_edge(b_vertex, d_vertex)

        e_block = Block()
        e_vertex = l.tree.add_vertex()
        l.blocks[e_vertex] = e_block
        l.tree.add_edge(b_vertex, e_vertex)

        # add 1 block f as d's child
        f_block = Block()
        f_vertex = l.tree.add_vertex()
        l.blocks[f_vertex] = f_block
        l.tree.add_edge(d_vertex, f_vertex)

        # add 1 block as f's child
        g_block = Block()
        g_vertex = l.tree.add_vertex()
        l.blocks[g_vertex] = g_block
        l.tree.add_edge(f_vertex, g_vertex)

        # add 1 block as g's child
        h_block = Block()
        h_vertex = l.tree.add_vertex()
        l.blocks[h_vertex] = h_block
        l.tree.add_edge(g_vertex, h_vertex)

        i_block = Block()
        self.assertEqual(l.fork_choice_rule(i_block).id, h_block.id)

        # ensure only the root is finalized, while forcing probability of error
        # to be 0
        self.assertTrue(l.is_finalized(l.blocks[l.root], 0.0))
        self.assertFalse(l.is_finalized(a_block, 0.0))
        self.assertFalse(l.is_finalized(b_block, 0.0))
        self.assertFalse(l.is_finalized(c_block, 0.0))
        self.assertFalse(l.is_finalized(d_block, 0.0))
        self.assertFalse(l.is_finalized(e_block, 0.0))
        self.assertFalse(l.is_finalized(f_block, 0.0))
        self.assertFalse(l.is_finalized(g_block, 0.0))
        self.assertFalse(l.is_finalized(h_block, 0.0))
        self.assertFalse(l.is_finalized(i_block, 0.0))

if __name__ == '__main__':
    unittest.main()
