import numpy as np, uuid, random 
from itertools import takewhile
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
    def fork_choice_rule(self):
        pass

    def common_prefix(self, main_chains=None):
        if main_chains is None:
            main_chains = self.main_chains()

        common_prefix = [v[0] for v in takewhile(lambda chain:
            chain.count(chain[0])==len(chain), zip(*main_chains))]

        return common_prefix

    def random_main_chain(self, main_chains=None):
        if main_chains is None:
            main_chains = self.main_chains()

        return random.choice(main_chains)

    @abstractmethod
    def main_chains(self):
        # find leaf blocks via fork choice rule
        leaf_blocks = self.fork_choice_rule()
        main_chains = []

        # traverse from leaf vertices up to root and add to main chain
        root_block = self.vertex_to_blocks[self.root]
        for leaf_block in leaf_blocks: 
            main_chains.append([])
            block = leaf_block
            while block.id!=root_block.id:
                main_chains[-1].append(block)
                parent_vertex = self.block_to_vertices[block.parent_id]
                block = self.vertex_to_blocks[parent_vertex]
            main_chains[-1].append(root_block)
            # reverse the path
            main_chains[-1] = main_chains[-1][::-1]

        return main_chains

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
        new_block.set_parent_id(parent_block.id)
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


class LongestChain(Algorithm):
    def fork_choice_rule(self):
        depth_array = self.depth.get_array()
        # find max depth
        max_depth = np.amax(depth_array)

        # find indices where depth is max depth
        max_indices = np.where(depth_array==np.amax(depth_array))[0]

        # copy blocks into parent blocks array
        it = np.nditer(max_indices, flags=['f_index'])
        parent_blocks = np.empty(shape=max_indices.shape[0], dtype=object)
        while not it.finished:
            parent_blocks[it.index] = self.vertex_to_blocks[self.tree.vertex(it[0])]
            it.iternext()

        return parent_blocks

class Prism(LongestChain):
    def __init__(self, num_voting_chains=10):
        # Initialize main proposer tree according to longest chain protocol
        super(LongestChain, self).__init__()

        # Initialize all voting chains
        self.num_voting_chains = num_voting_chains
        self.voting_chains = []


        for i in range(0, self.num_voting_chains):
            self.voting_chains.append(LongestChain())

    def set_block_chain(self, block):
        choice = np.random.randint(0, self.num_voting_chains+1)

        # Selection of 0 corresponds to adding to proposer tree
        if choice==0:
            block.set_block_type('proposer')
        else:
            block.set_block_type('voter', choice-1)

    def add_block_by_fork_choice_rule(self, block):
        # Choose which type of block
        self.set_block_chain(block)

        if block.block_type=='proposer':
            print(f'adding {block.block_type} block to main chain')
        else:
            print(f'adding {block.block_type} block to chain {block.block_chain}')
        if block.block_type=='proposer':
            # If proposer block, call LongestChain's add_block_by_fork_choice_rule
            return super(Prism, self).add_block_by_fork_choice_rule(block)
        else:
            # If voting block, call LongestChain's add_block_by_fork_choice_rule
            # on specified chain
            parent_block = self.voting_chains[block.block_chain].add_block_by_fork_choice_rule(block)

            # Find max depth voted by parent
            max_voted_depth = -1
            for referenced_block in parent_block.referenced_blocks:
                vertex = self.block_to_vertices[referenced_block.id]
                if self.depth[vertex]>max_voted_depth:
                    max_voted_depth = self.depth[vertex]

            vote_depth = max_voted_depth+1

            # Get depth array
            depth_array = self.depth.get_array()

            # Find indices where depth is greater than max depth voted by parent
            while True:
                choices = np.where(depth_array==vote_depth)[0]
                # Exhausted depth of proposer tree
                if len(choices)==0:
                    break
                voted_block = self.vertex_to_blocks[self.tree.vertex(np.random.choice(choices))]
                block.add_referenced_block(voted_block)
                vote_depth+=1

            return parent_block


    def fork_choice_rule(self, chain='main'):
        if chain=='main':
            # If adding to main proposer blocktree, call LongestChain's fork
            # choice rule
            return super(Prism, self).fork_choice_rule()
        else:
            # If adding to voter blocktree, call LongestChain's fork choice rule
            # on specified blocktree
            return self.voting_chains[chain].fork_choice_rule()

    def main_chains(self):
        # Call LongestChain's main_chains function on proposer tree
        proposer_tree_main_chains = super(Prism, self).main_chains()

        main_chains = []
        
        # Add all blocks referenced by proposer blocks
        for main_chain in proposer_tree_main_chains:
            main_chains.append([])
            for proposer_block in main_chain:
                added_blocks = list(proposer_block.referenced_blocks)
                added_blocks.append(proposer_block)
                main_chains[-1]+=added_blocks
         
        return main_chains

class LongestChainWithPool(LongestChain):
    def __init__(self, block_size=50):
        super(LongestChainWithPool, self).__init__()
        self.pool_blocks = np.array([])
        self.max_referenced_blocks = 10*block_size

    def add_pool_block(self, new_pool_block):
        self.pool_blocks = np.append(self.pool_blocks, new_pool_block)

    def add_block(self, parent_block, new_block):
        # call LongestChain's add_block function
        super(LongestChainWithPool, self).add_block(parent_block, new_block)

        if self.pool_blocks.shape[0]>0:
            it = np.nditer(self.pool_blocks, flags=['f_index', 'refs_ok'])

            while not it.finished: #and new_block.referenced_blocks.shape[0]<=self.max_referenced_blocks:
                pool_block = self.pool_blocks[it.index]
                new_block.add_referenced_block(pool_block)
                it.iternext()

            self.pool_blocks = np.array([])

    def main_chains(self):
        # call LongestChain's main_chains function
        tree_main_chains = super(LongestChainWithPool, self).main_chains()

        main_chains = []

        for main_chain in tree_main_chains:
            main_chains.append([])
            for tree_block in main_chain:
                added_blocks = list(tree_block.referenced_blocks)
                added_blocks.append(tree_block)
                main_chains[-1]+=added_blocks

        return main_chains


class GHOST(Algorithm):
    def __init__(self, validate_length=True):
        super(GHOST, self).__init__()
        self.subtree_size = self.tree.new_vertex_property('int')
        self.subtree_size[self.root] = 0
        self.validate_length = validate_length

    def main_chains(self):
        # call Algorithm's main_chains function
        main_chains = super(GHOST, self).main_chains()

        if self.validate_length:
            depths = self.depth.get_array()
            max_depth = np.amax(depths)
            assert max_depth+1==len(main_chains[0]), 'Mismatch between Longest Chain Main Chain and GHOST Main Chain'

        return main_chains

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

