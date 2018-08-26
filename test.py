import unittest
from messages import Block

class TestBlockchainSimulator(unittest.TestCase):
    def test_block_tree(self):
        root = Block(None)

        a = Block(root.id)
        b = Block(root.id)
        root.add_child(a)
        root.add_child(b)

        c = Block(a.id)
        d = Block(b.id)
        e = Block(b.id)
        f = Block(b.id)
        a.add_child(c)
        b.add_child(d)
        b.add_child(e)
        b.add_child(f)

        g = Block(f.id)
        f.add_child(g)

        h = Block(e.id)
        i = Block(e.id)
        d.add_child(h)
        d.add_child(i)

        j = Block(i.id)
        i.add_child(j)

        longest_chain_block, longest_chain_length = root.longest_chain()

        self.assertEqual(4, longest_chain_length)
        self.assertEqual(j.id, longest_chain_block.id)

if __name__ == '__main__':
    unittest.main()
