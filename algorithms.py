import numpy as np, uuid, random 
from itertools import takewhile
from graph_tool import *
import graph_tool.all as gt
from math import e, factorial
from block import Block
from abc import ABC, abstractmethod
from constants import FINALIZATION_DEPTH

def compute_finalization_depth(epsilon, num_nodes, num_adversaries):
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

    def get_block_by_id(self, id):
        if id in self.block_to_vertices:
            vertex = self.block_to_vertices[id]
            return self.vertex_to_blocks[vertex]

    def random_main_chain(self, main_chains=None):
        if main_chains is None:
            main_chains = self.main_chains()

        return random.choice(main_chains)

    @abstractmethod
    def fork_choice_rule(self):
        pass

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

    def common_prefix(self, main_chains=None):
        if main_chains is None:
            main_chains = self.main_chains()

        common_prefix = [v[0] for v in takewhile(lambda chain:
            chain.count(chain[0])==len(chain), zip(*main_chains))]

        return common_prefix

    # add a new block given a parent block
    def add_block_by_parent(self, new_block, parent_block):
        new_vertex = self.tree.add_vertex()
        self.vertex_to_blocks[new_vertex] = new_block
        self.block_to_vertices[new_block.id] = new_vertex

        parent_vertex = self.block_to_vertices[parent_block.id]

        self.tree.add_edge(parent_vertex, new_vertex)
        self.depth[new_vertex] = self.depth[self.tree.vertex(parent_vertex)]+1
        new_block.set_parent_id(parent_block.id)
        new_block.set_depth(parent_block.depth+1)

        return parent_block

    # add block based on fork choice rule
    def add_block_by_fork_choice_rule(self, new_block):
        parent_block = self.fork_choice_rule()[0]
        self.add_block_by_parent(new_block, parent_block)
        return parent_block

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
            voting_chain = LongestChain()
            self.voting_chains.append(voting_chain)

    def get_referenced_blocks(self, proposer_block_id):
        if proposer_block_id in self.block_to_vertices:
            proposer_vertex = self.block_to_vertices[proposer_block_id]
            proposer_block = self.vertex_to_blocks[proposer_vertex] 
            if proposer_vertex!=self.root:
                return proposer_block.referenced_blocks
        return []

    def set_block_chain(self, block):
        choice = np.random.randint(0, self.num_voting_chains+1)

        # Selection of 0 corresponds to adding to proposer tree
        if choice==0:
            block.set_block_type('proposer')
        else:
            block.set_block_type('voter', choice-1)

    def add_block_by_parent(self, new_block, parent_block):
        if new_block.block_type=='proposer':
            # If proposer block, call LongestChain's add_block_by_parent
            return super(Prism, self).add_block_by_parent(new_block,
                    parent_block)
        else:
            # If voting block, call LongestChain's add_block_by_parent
            # on specified chain
            choice = np.random.randint(0, self.num_voting_chains)
            new_block.set_block_type('voter', choice)
            voting_chain = self.voting_chains[new_block.block_chain]
            parent_block = voting_chain.add_block_by_fork_choice_rule(new_block)

            voting_chain_genesis = voting_chain.vertex_to_blocks[voting_chain.root]

            # Find max depth voted by parent and have new block vote for all
            # subsequent depths up to its own
            if parent_block.id==voting_chain_genesis.id:
                new_block.set_max_voted_block_depth(0)
                vote_depth = 1
            else:
                new_block.set_max_voted_block_depth(parent_block.max_voted_block_depth)
                vote_depth = parent_block.max_voted_block_depth+1

            block_depth = voting_chain.depth[voting_chain.block_to_vertices[new_block.id]]
            # Get depth array
            depth_array = self.depth.get_array()

            # Find indices where depth is greater than max depth voted by parent
            while vote_depth<=block_depth:
                choices = np.where(depth_array==vote_depth)[0]
                # Exhausted depth of proposer tree
                if len(choices)==0:
                    break
                voted_block = self.vertex_to_blocks[self.tree.vertex(np.random.choice(choices))]
                new_block.add_referenced_block(voted_block)
                voted_block.add_referenced_block(new_block)
                new_block.set_max_voted_block_depth(vote_depth)
                vote_depth+=1

            return parent_block

    def add_block_by_fork_choice_rule(self, block):
        # Choose which type of block
        self.set_block_chain(block)

        if block.block_type=='proposer':
            # If proposer block, call LongestChain's add_block_by_fork_choice_rule
            return super(Prism, self).add_block_by_fork_choice_rule(block)
        else:
            # If voting block, call LongestChain's add_block_by_fork_choice_rule
            # on specified chain
            voting_chain = self.voting_chains[block.block_chain]
            parent_block = voting_chain.add_block_by_fork_choice_rule(block)

            voting_chain_genesis = voting_chain.vertex_to_blocks[voting_chain.root]

            # Find max depth voted by parent and have new block vote for all
            # subsequent depths up to its own
            if parent_block.id==voting_chain_genesis.id:
                block.set_max_voted_block_depth(0)
                vote_depth = 1
            else:
                block.set_max_voted_block_depth(parent_block.max_voted_block_depth)
                vote_depth = parent_block.max_voted_block_depth+1

            block_depth = voting_chain.depth[voting_chain.block_to_vertices[block.id]]
            # Get depth array
            depth_array = self.depth.get_array()

            # Find indices where depth is greater than max depth voted by parent
            while vote_depth<=block_depth:
                choices = np.where(depth_array==vote_depth)[0]
                # Exhausted depth of proposer tree
                if len(choices)==0:
                    break
                voted_block = self.vertex_to_blocks[self.tree.vertex(np.random.choice(choices))]
                block.add_referenced_block(voted_block)
                voted_block.add_referenced_block(block)
                block.set_max_voted_block_depth(vote_depth)
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
        depth = 1

        # tabulate votes for all blocks
        vote_dict = {}
        for voting_chain in self.voting_chains:
            main_voting_chain = voting_chain.main_chains()[0]
            for block in main_voting_chain:
                if block.id!='Genesis':
                    for voted_block in block.referenced_blocks:
                        if voted_block.id not in vote_dict:
                            vote_dict[voted_block.id]=0
                        vote_dict[voted_block.id]+=1

        # Get depth array
        depth_array = self.depth.get_array()
        depth = 1

        main_chains = [[self.vertex_to_blocks[self.root]]]
        while True:
            vertices_at_depth = np.where(depth_array==depth)[0]
            # Exhausted depth of proposer tree
            if len(vertices_at_depth)==0:
                break
            max_votes = 0
            max_voted_block = None
            for vertex in vertices_at_depth:
                if self.vertex_to_blocks[vertex].id in vote_dict:
                    votes = vote_dict[self.vertex_to_blocks[vertex].id]
                else:
                    votes = 0
                if votes>=max_votes:
                    max_votes = votes
                    max_voted_block = self.vertex_to_blocks[vertex]

            main_chains[0]+=list(max_voted_block.referenced_blocks)
            main_chains[0].append(max_voted_block)
            depth+=1
        return main_chains
            
class LongestChainWithPool(LongestChain):
    def __init__(self, block_size=50):
        super(LongestChainWithPool, self).__init__()
        self.pool_blocks = np.array([])
        self.max_referenced_blocks = 10*block_size

    def add_pool_block(self, new_pool_block):
        self.pool_blocks = np.append(self.pool_blocks, new_pool_block)

    def add_tree_block(self, new_block):
        super(LongestChainWithPool, self).add_block_by_fork_choice_rule(new_block)

        if self.pool_blocks.shape[0]>0:
            it = np.nditer(self.pool_blocks, flags=['f_index', 'refs_ok'])

            while not it.finished: #and new_block.referenced_blocks.shape[0]<=self.max_referenced_blocks:
                pool_block = self.pool_blocks[it.index]
                new_block.add_referenced_block(pool_block)
                it.iternext()

            self.pool_blocks = np.array([])

    def add_block_by_fork_choice_rule(self, new_block):
        if new_block.block_type=='pool':
            self.add_pool_block(new_block)
        elif new_block.block_type=='tree':
            self.add_tree_block(new_block)

    def main_chains(self):
        # call LongestChain's main_chains function
        tree_main_chains = super(LongestChainWithPool, self).main_chains()

        main_chains = []
        for main_chain in tree_main_chains:
            main_chains.append([])
            for tree_block in main_chain:
                if self.block_to_vertices[tree_block.id]!=self.root:
                    main_chains[-1]+=list(tree_block.referenced_blocks)
                main_chains[-1].append(tree_block)

        return main_chains


class GHOST(Algorithm):
    def __init__(self, validate_length=False):
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

    def add_block_by_fork_choice_rule(self, new_block):
        # call Algorithm's add_block function
        super(GHOST, self).add_block_by_fork_choice_rule(new_block)

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

