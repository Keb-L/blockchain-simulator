iport numpy as np, uuid
from graph_tool import *
import graph_tool.all as gt
from math import e, factorial
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
    def is_finalized(self, block, params):
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

    def compute_k(self, epsilon, _lambda, num_nodes, num_adversaries):
        # compute finalization depth
        k = 0
        q = float(num_adversaries)/num_nodes
        p = 1-q
        while True:
            s = 0
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
        for v in self.tree.vertices():
            if self.blocks[v]==block:
                source = v

        epsilon = params['tx_error_prob']

        finalization_depth = self.compute_k(epsilon, params['proposal_rate'], params['num_nodes'],
                params['num_adversaries'])

        is_valid_depth = finalization_depth in gt.shortest_distance(self.tree,
                source, max_dist=finalization_depth).get_array()

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
        self.blocks[new_vertex] = new_block

        max_subtree_vertex = self.heaviest_subtree()
        self.tree.add_edge(max_subtree_vertex, new_vertex)
        return self.blocks[max_subtree_vertex]

    '''
    Both LongestChain() and GHOST() have the same finalization protocol, hence
    the code is identical. TODO: find a better implementation of code reuse
    '''
    def compute_k(self, epsilon, _lambda, num_nodes, num_adversaries):
        # compute finalization depth
        k = 0
        q = float(num_adversaries)/num_nodes
        p = 1-q
        while True:
            s = 0
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
        for v in self.tree.vertices():
            if self.blocks[v]==block:
                source = v

        epsilon = params['tx_error_prob']

        finalization_depth = self.compute_k(epsilon, params['proposal_rate'], params['num_nodes'],
                params['num_adversaries'])

        is_valid_depth = finalization_depth in gt.shortest_distance(self.tree,
                source, max_dist=finalization_depth).get_array()

        # compute whether or not there is an error in transaction confirmation
        error = False if np.random.uniform(0, 1)<=1-epsilon else True

        finalized = True if is_valid_depth and not error else False

        return finalized

    def main_chain(self):
        max_subtree_vertex = self.heaviest_subtree()
        main_chain = gt.shortest_path(self.tree, self.root, max_subtree_vertex)
        return main_chain
