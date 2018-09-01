import numpy as np, uuid
from graph_tool import *
import graph_tool.all as gt
from block import Block
from abc import ABC, abstractmethod
from constants import FINALIZATION_DEPTH

class Algorithm():
    def __init__(self):
        self.tree = Graph()
        self.blocks = self.tree.new_vertex_property('object')

        self.root = self.tree.add_vertex()
        self.blocks[self.root] = Block(id='Genesis')

    @abstractmethod
    def fork_choice_rule(self, new_block):
        pass

    @abstractmethod
    def is_finalized(self, block, epsilon):
        pass

    @abstractmethod
    def main_chain(self):
        pass

    def add_block(self, new_block):
        # create new vertex
        new_vertex = self.tree.add_vertex()
        self.blocks[new_vertex] = new_block

        parent_id = new_block.parent_id
        parent_vertex = None
        parent_block = None
        # look through all blocks and find appropriate parent block
        for vertex in self.tree.vertices():
            if self.blocks[vertex].id==parent_id:
                parent_vertex = vertex
                parent_block = self.blocks[vertex]
                self.tree.add_edge(parent_vertex, new_vertex)
                break
        return parent_block

    def graph_to_str(self, vertex=None, level=0):
        if vertex==None:
            vertex=self.root
        ret = '   '*level+f'{self.blocks[vertex].id}\n'
        for e in vertex.out_edges():
            child = e.target()	
            ret += self.graph_to_str(vertex=child, level=level+1)
        return ret

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

    def is_finalized(self, block, epsilon):
        # search for starting block
        for v in self.tree.vertices():
            if self.blocks[v]==block:
                source = v

        is_valid_depth = FINALIZATION_DEPTH in gt.shortest_distance(self.tree,
                source, max_dist=FINALIZATION_DEPTH).get_array()

        # compute whether or not there is an error in transaction confirmation
        error = False if np.random.uniform(0, 1)<=1-epsilon else True

        finalized = True if is_valid_depth and not error else False

        return finalized

    def main_chain(self):
        # find leafs of tree by determining which nodes have out degree 0
        out_degrees = self.tree.get_out_degrees(self.tree.get_vertices())
        leaf_indices = np.where(out_degrees == 0)[0]
        
        # find main chain
        max_len = 0
        main_chain = np.array([])
        index = 0 
        for v in self.tree.vertices():
            if index in leaf_indices:
                chain = gt.shortest_path(self.tree, self.root, v)
                if len(chain[0])>max_len:
                    main_chain = chain[0]
                    max_len = len(chain[0])
            index+=1

        return main_chain

class GHOST(Algorithm):
    def fork_choice_rule(self, new_block):
        return

    def is_finalized(self, block, epsilon):
        return

    def main_chain(self):
        return
