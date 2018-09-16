import numpy as np, uuid, functools
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

    def common_prefix(self, main_chains=None):
        if main_chains is None:
            main_chains = self.main_chains()

        l = [functools.reduce(lambda v1, v2: v1 if self.vertex_to_blocks[v1].id ==
            self.vertex_to_blocks[v2].id else None,
            chain) for chain in zip(*main_chains)] + [None]

        common_prefix = l[:l.index(None)]

        return common_prefix

    @abstractmethod
    def main_chains(self):
        # find leaf blocks via fork choice rule
        leaf_blocks = self.fork_choice_rule()

        main_chain = []

        # traverse from leaf vertices up to root and add to main chain
        for leaf_block in leaf_blocks: 
            main_chain.append([])
            vertex = self.block_to_vertices[leaf_block.id]
            while vertex!=self.root:
                main_chain[-1].append(vertex)
                block = self.vertex_to_blocks[vertex]
                vertex = self.block_to_vertices[block.parent_id]
            main_chain[-1].append(self.root)
            # reverse the path
            main_chain[-1] = main_chain[-1][::-1]

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
        parent_block = self.fork_choice_rule()[0]
        new_block.parent_id = parent_block.id
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
        depths = self.depth.get_array()
        max_depth = np.amax(depths)
        max_indices = np.where(depths==max_depth)[0]
        parent_blocks = [self.vertex_to_blocks[self.tree.vertex(index)] for index in
                max_indices]

        return parent_blocks

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

        # set subtree size of leaf vertex to be 0
        vertex = self.block_to_vertices[new_block.id]
        self.subtree_size[vertex] = 0

        # increment subtree size for all blocks along path from root to new leaf
        # vertex
        while vertex!=self.root:
            block = self.vertex_to_blocks[vertex]
            vertex = self.block_to_vertices[block.parent_id]
            self.subtree_size[vertex]+=1

    def fork_choice_rule(self):
        # start with root vertex
        max_subtree_vertices = [self.root]
        children = []
        for vertex in max_subtree_vertices:
            children+=list(self.root.out_edges())

        # search for leaf vertex
        while len(children)!=0:
            max_subtree_size = 0
            max_subtree_vertices = []
            # search for child with max subtree size
            for edge in children:
                target = edge.target()
                if self.subtree_size[target]>max_subtree_size:
                    max_subtree_vertices = [target]
                    max_subtree_size = self.subtree_size[target]
                elif self.subtree_size[target]==max_subtree_size:
                    max_subtree_vertices.append(target)
            children = []
            for vertex in max_subtree_vertices:
                children+=list(vertex.out_edges())

        parent_blocks = [self.vertex_to_blocks[vertex] for vertex in
                max_subtree_vertices]

        return parent_blocks


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
        return 6
