import numpy as np, uuid
from graph_tool import *
import graph_tool.all as gt
from block import Block

class Algorithm():
    def __init__(self):
        self.tree = Graph()
        self.blocks = self.tree.new_vertex_property('object')

        self.root = self.tree.add_vertex()
        self.blocks[self.root] = Block()

    def graph_to_str(self):
        s = ''
        for e in gt.bfs_iterator(self.tree, self.tree.vertex(0)):
            s+=f'{self.blocks[e.source()].id} -> {self.blocks[e.target()].id}\n'
        return s

class LongestChain(Algorithm):
    def fork_choice_rule(self, new_block):
        new_vertex = self.tree.add_vertex()
        self.blocks[new_vertex] = new_block
        # start at root vertex
        parent_vertex = self.root
        # lowest level in bfs iterator returns longest chain
        for e in gt.bfs_iterator(self.tree, self.tree.vertex(0)):
            parent_vertex = e.target()
        self.tree.add_edge(parent_vertex, new_vertex)
        return self.blocks[parent_vertex]
