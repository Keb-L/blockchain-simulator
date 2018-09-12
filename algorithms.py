import numpy as np, uuid
from graph_tool import *
import graph_tool.all as gt
from math import e, factorial
from block import Block
from abc import ABC, abstractmethod
from constants import FINALIZATION_DEPTH

class Algorithm():
    def __init__(self):
        self.tree = Graph()
        # maps vertex to block
        self.vertex_to_blocks = self.tree.new_vertex_property('object')
        # maps block to vertex
        self.block_to_vertices = {}
        # create a new vertex property corresponding to depth
        self.depth = self.tree.new_vertex_property('int')

        # add genesis block and vertex
        self.root = self.tree.add_vertex()
        genesis = Block(id='Genesis')
        self.vertex_to_blocks[self.root] = genesis
        self.block_to_vertices[genesis.id] = self.root
        self.depth[self.root] = 0

    @abstractmethod
    def fork_choice_rule(self, new_block):
        pass

    @abstractmethod
    def main_chain(self):
        leaf_block = self.fork_choice_rule()
        leaf_vertex = self.block_to_vertices[leaf_block.id]
        main_chain = gt.shortest_path(self.tree, self.root,
                leaf_vertex)[0]
        return main_chain

    # add a new block given a parent block
    def add_block(self, parent_block, new_block):
        # create new vertex
        new_vertex = self.tree.add_vertex()
        self.vertex_to_blocks[new_vertex] = new_block
        self.block_to_vertices[new_block.id] = new_vertex

        parent_vertex = self.block_to_vertices[parent_block.id]

        self.tree.add_edge(parent_vertex, new_vertex)
        self.depth[new_vertex] = self.depth[self.tree.vertex(parent_vertex)]+1

    # add block based on fork choice rule
    def add_block_by_fork_choice_rule(self, new_block):
        parent_block = self.fork_choice_rule()
        self.add_block(parent_block, new_block)

        return parent_block

    # adds block based on parent id
    def add_block_by_parent_id(self, new_block):
        parent_id = new_block.parent_id

        # if parent id is in mapping, add the block and return the block.
        # otherwise, return None
        if parent_id in self.block_to_vertices:
            parent_vertex = self.block_to_vertices[parent_id]
            parent_block = self.vertex_to_blocks[parent_vertex]
            self.add_block(parent_block, new_block)
            return parent_block
        else:
            return None

    def graph_to_str(self, vertex=None, level=0):
        if vertex==None:
            vertex=self.root
        ret = '   '*level+f'{self.vertex_to_blocks[vertex].id}\n'
        for e in vertex.out_edges():
            child = e.target()	
            ret += self.graph_to_str(vertex=child, level=level+1)
        return ret

class LongestChain(Algorithm):
    def fork_choice_rule(self):
        # parent vertex is vertex with maximum depth
        parent_vertex = self.tree.vertex(self.depth.get_array().argmax(axis=0))
        parent_block = self.vertex_to_blocks[parent_vertex]

        return parent_block

    def compute_k(self, epsilon, num_nodes, num_adversaries):
        # compute finalization depth
        k = 0
        q = float(num_adversaries)/num_nodes
        p = 1-q
        while True:
            s = 0
            _lambda = k*q/p
            for i in range(0, k):
                s+=pow(_lambda, i)*pow(e, -_lambda)/factorial(i)*(1-pow(q/p, k-i))
            result = 1-s
            if result<=epsilon:
                break
            else:
                k+=1
        return 6
        # return k

class GHOST(Algorithm):
    def __init__(self):
        super(GHOST, self).__init__()
        self.subtree_size = {}

        self.subtree_size[self.root] = 0

    def add_block(self, parent_block, new_block):
        # call Algorithm's add_block function
        super(GHOST, self).add_block(parent_block, new_block)

        # increment subtree size for all blocks along path from root to new leaf
        # vertex
        leaf_vertex = self.block_to_vertices[new_block.id]
        path = gt.shortest_path(self.tree, self.root, leaf_vertex)[0] 

        for vertex in path[:-1]:
            self.subtree_size[vertex]+=1
        # set subtree size of leaf vertex to be 0
        self.subtree_size[leaf_vertex]=0

    def fork_choice_rule(self):
        # parent vertex is vertex with maximum size subtree
        max_subtree_vertex = max(self.subtree_size, key=self.subtree_size.get)
        parent_block = self.vertex_to_blocks[max_subtree_vertex]

        return parent_block

    '''
    Both LongestChain() and GHOST() have the same finalization protocol, hence
    the code is identical. TODO: find a better implementation of code reuse
    '''
    def compute_k(self, epsilon, num_nodes, num_adversaries):
        # compute finalization depth
        k = 0
        q = float(num_adversaries)/num_nodes
        p = 1-q
        while True:
            s = 0
            _lambda = k*q/p
            for i in range(0, k):
                s+=pow(_lambda, i)*pow(e, -_lambda)/factorial(i)*(1-pow(q/p, k-i))
            result = 1-s
            if result<=epsilon:
                break
            else:
                k+=1
        return k
