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
    def is_finalized(self, block, params):
        pass

    @abstractmethod
    def main_chain(self):
        pass

    def add_block(self, new_block):
        # create new vertex
        new_vertex = self.tree.add_vertex()
        self.vertex_to_blocks[new_vertex] = new_block
        self.block_to_vertices[new_block.id] = new_vertex

        parent_id = new_block.parent_id

        # if parent id is in mapping, add the block and return the block.
        # otherwise, return None
        if parent_id in self.block_to_vertices:
            parent_vertex = self.block_to_vertices[parent_id]
            parent_block = self.vertex_to_blocks[parent_vertex]
            self.tree.add_edge(parent_vertex, new_vertex)
            self.depth[new_vertex] = self.depth[self.tree.vertex(parent_vertex)]+1
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
    def fork_choice_rule(self, new_block):
        new_vertex = self.tree.add_vertex()
        self.vertex_to_blocks[new_vertex] = new_block
        self.block_to_vertices[new_block.id] = new_vertex
        # start at root vertex
        parent_vertex = self.root

        # parent vertex is vertex with maximum depth
        parent_vertex = self.tree.vertex(self.depth.get_array().argmax(axis=0))

        # add new node based on parent vertex
        self.tree.add_edge(parent_vertex, new_vertex)
        self.depth[new_vertex] = self.depth[self.tree.vertex(parent_vertex)]+1

        return self.vertex_to_blocks[parent_vertex]

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

    def is_finalized(self, block, params):
        # search for starting block
        source = self.block_to_vertices[block.id]

        epsilon = params['tx_error_prob']

        finalization_depth = self.compute_k(epsilon, params['num_nodes'],
                params['num_adversaries'])

        current_depth = self.depth[self.tree.vertex(source)]

        is_valid_depth = current_depth >= finalization_depth

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
    def heaviest_subtree_helper(self, vertex):
        if vertex is None:
            vertex = self.root
        s = 0
        for e in vertex.out_edges():
            s+=self.heaviest_subtree_helper(e.target())
        return vertex.out_degree()+s

    def heaviest_subtree(self): 
        vertex = self.root
        while True:
            max_subtree_vertex = None
            max_subtree_size = -1
            for e in vertex.out_edges():
                size = self.heaviest_subtree_helper(e.target())
                if size>max_subtree_size:
                    max_subtree_vertex = e.target()
                    max_subtree_size = size
            if max_subtree_size==0:
                return max_subtree_vertex
            else:
                vertex=max_subtree_vertex
        return None

    def fork_choice_rule(self, new_block):
        new_vertex = self.tree.add_vertex()
        self.vertex_to_blocks[new_vertex] = new_block
        self.block_to_vertices[new_block.id] = new_vertex

        max_subtree_vertex = self.heaviest_subtree()
        self.tree.add_edge(max_subtree_vertex, new_vertex)
        self.depth[new_vertex] = self.depth[self.tree.vertex(parent_vertex)]+1
        return self.vertex_to_blocks[max_subtree_vertex]

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

    def is_finalized(self, block, params):
        # search for starting block
        source = self.block_to_vertices[block.id]

        epsilon = params['tx_error_prob']

        finalization_depth = self.compute_k(epsilon, params['num_nodes'],
                params['num_adversaries'])

        current_depth = self.depth[self.tree.vertex(source)]

        is_valid_depth = current_depth >= finalization_depth

        # compute whether or not there is an error in transaction confirmation
        error = False if np.random.uniform(0, 1)<=1-epsilon else True

        finalized = True if is_valid_depth and not error else False

        return finalized

    def main_chain(self):
        max_subtree_vertex = self.heaviest_subtree()
        main_chain = gt.shortest_path(self.tree, self.root, max_subtree_vertex)
        return main_chain
