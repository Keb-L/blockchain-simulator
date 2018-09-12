import unittest
from algorithms import *
from block import Block

class TestBlockchainSimulator(unittest.TestCase):
    def test_longest_chain(self):
        l = LongestChain()
        # create our own tree 
        l.tree = Graph()
        l.root = l.tree.add_vertex()
        l.vertex_to_blocks[l.root] = Block(id='Genesis')

        # add 2 vertex_to_blocks a and b as root's children
        a_block = Block()
        a_vertex = l.tree.add_vertex()
        l.vertex_to_blocks[a_vertex] = a_block
        l.tree.add_edge(l.root, a_vertex)

        b_block = Block()
        b_vertex = l.tree.add_vertex()
        l.vertex_to_blocks[b_vertex] = b_block
        l.tree.add_edge(l.root, b_vertex)

        # add 1 block c as a's child
        c_block = Block()
        c_vertex = l.tree.add_vertex()
        l.vertex_to_blocks[c_vertex] = c_block
        l.tree.add_edge(a_vertex, c_vertex)

        # add 2 vertex_to_blocks d and e as b's children
        d_block = Block()
        d_vertex = l.tree.add_vertex()
        l.vertex_to_blocks[d_vertex] = d_block
        l.tree.add_edge(b_vertex, d_vertex)

        e_block = Block()
        e_vertex = l.tree.add_vertex()
        l.vertex_to_blocks[e_vertex] = e_block
        l.tree.add_edge(b_vertex, e_vertex)

        # add 1 block f as d's child
        f_block = Block()
        f_vertex = l.tree.add_vertex()
        l.vertex_to_blocks[f_vertex] = f_block
        l.tree.add_edge(d_vertex, f_vertex)

        # add 1 block as f's child
        g_block = Block()
        g_vertex = l.tree.add_vertex()
        l.vertex_to_blocks[g_vertex] = g_block
        l.tree.add_edge(f_vertex, g_vertex)

        # add 1 block as g's child
        h_block = Block()
        h_vertex = l.tree.add_vertex()
        l.vertex_to_blocks[h_vertex] = h_block
        l.tree.add_edge(g_vertex, h_vertex)

        i_block = Block()


    def test_GHOST(self):
        g = GHOST()
        # create our own tree 
        g.tree = Graph()
        g.root = g.tree.add_vertex()
        g.vertex_to_blocks[g.root] = Block(id='Genesis')

        # add 2 vertex_to_blocks a and b as root's children
        a_block = Block()
        a_vertex = g.tree.add_vertex()
        g.vertex_to_blocks[a_vertex] = a_block
        g.tree.add_edge(g.root, a_vertex)

        b_block = Block()
        b_vertex = g.tree.add_vertex()
        g.vertex_to_blocks[b_vertex] = b_block
        g.tree.add_edge(g.root, b_vertex)

        # add 4 vertex_to_blocks c, d, e, f as a's children
        c_block = Block()
        c_vertex = g.tree.add_vertex()
        g.vertex_to_blocks[c_vertex] = c_block
        g.tree.add_edge(a_vertex, c_vertex)

        d_block = Block()
        d_vertex = g.tree.add_vertex()
        g.vertex_to_blocks[d_vertex] = d_block
        g.tree.add_edge(a_vertex, d_vertex)

        e_block = Block()
        e_vertex = g.tree.add_vertex()
        g.vertex_to_blocks[e_vertex] = e_block
        g.tree.add_edge(a_vertex, e_vertex)

        f_block = Block()
        f_vertex = g.tree.add_vertex()
        g.vertex_to_blocks[f_vertex] = f_block
        g.tree.add_edge(a_vertex, f_vertex)

        # add 1 block g as b's child
        g_block = Block()
        g_vertex = g.tree.add_vertex()
        g.vertex_to_blocks[g_vertex] = g_block
        g.tree.add_edge(b_vertex, g_vertex)

        # add 1 block h as g's child
        h_block = Block()
        h_vertex = g.tree.add_vertex()
        g.vertex_to_blocks[h_vertex] = h_block
        g.tree.add_edge(g_vertex, h_vertex)

        i_block = Block()

if __name__ == '__main__':
    unittest.main()
