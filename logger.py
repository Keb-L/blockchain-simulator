import csv, json
from algorithms import compute_finalization_depth
from graph_tool.all import *
from network import constant_decker_wattenhorf
from constants import TX_SIZE

def log_blocks(params, proposals):
    with open('./logs/blocks.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 
                    'parent id', 
                    'block type',
                    'proposal timestamp', 
                    'finalization timestamp', 
                    'depth', 
                    'finalized', 
                    'transactions']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for proposal in proposals:
            block = proposal.block
            tx_str = ';'.join(tx.id for tx in block.txs)
            depth = block.depth
            is_finalized = False if block.finalization_timestamp==None else True
            writer.writerow({
                'id': f'{block.id}', 
                'parent id': f'{block.parent_id}', 
                'block type': f'{block.block_type}', 
                'proposal timestamp': f'{block.proposal_timestamp}', 
                'finalization timestamp': f'{block.finalization_timestamp}', 
                'depth': f'{depth}',
                'finalized': f'{is_finalized}', 
                'transactions': f'{tx_str}'})
            if hasattr(block, 'referenced_blocks'):
                for ref_block in block.referenced_blocks:
                    ref_block_tx_str = ';'.join(tx.id for tx in ref_block.txs)
                    writer.writerow({
                        'id': f'{ref_block.id}', 
                        'parent id': f'{ref_block.parent_id}', 
                        'proposal timestamp': f'{ref_block.proposal_timestamp}', 
                        'finalization timestamp': f'{block.finalization_timestamp}', 
                        'depth': f'NA',
                        'finalized': f'{is_finalized}',
                        'transactions': f'{ref_block_tx_str}'
                        })

def log_txs(txs):
    with open('./logs/transactions.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'source node', 'generated timestamp', 'complete', 
                'main chain arrival timestamp', 
                'finalization timestamps']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for tx in txs:
            if tx.finalization_timestamps is None:
                finalization_timestamp_str = None
            else:
                finalization_timestamp_str = ';'.join(str(t) for t in
                        tx.finalization_timestamps)
            writer.writerow({'id': f'{tx.id}', 'source node':
                f'{tx.source.node_id}', 'generated timestamp':
                f'{tx.timestamp}', 'complete': f'{tx.complete}',
                'main chain arrival timestamp':
                f'{tx.main_chain_timestamp}',
                f'finalization timestamps':
                f'{finalization_timestamp_str}'})

def log_statistics(params, global_main_chain, proposals, time_elapsed):
    with open('./logs/stats.csv', 'w+') as csvfile:
        csvfile.write(json.dumps(params)+'\n')
        csvfile.write(f'Time elapsed,{time_elapsed}\n')

        delta_blocks = constant_decker_wattenhorf(params['max_block_size'])
        delta_txs = constant_decker_wattenhorf(TX_SIZE)
        f = params['tree_proposal_rate']
        # log network latency information
        if params['model']=='Decker-Wattenhorf' or params['model']=='Constant-Decker-Wattenhorf':
            csvfile.write(f'Average network latency for blocks (sec),{delta_blocks}\n')
            csvfile.write(f'Average network latency for txs (sec),{delta_txs}\n')
        if params['model']=='Zero':
            csvfile.write(f'Average network latency for blocks (sec),0\n')
            csvfile.write(f'Average network latency for txs (sec),0\n')

        # log finalization depth
        finalization_depth = compute_finalization_depth(params['tx_error_prob'], params['num_nodes'], params['num_adversaries'])
        csvfile.write(f'Finalization depth,{finalization_depth}\n')

        # log main chain information blocks
        num_blocks = len(list(filter(lambda proposal:
            proposal.block.block_type=='tree' or
            proposal.block.block_type=='proposer', proposals)))
        # filter main chain to only have tree blocks
        main_chain = list(filter(lambda block: block.block_type=='tree' or
            block.block_type=='proposer',
            global_main_chain))
        main_chain_length = len(main_chain)
        num_orphan_blocks = num_blocks - main_chain_length 
        csvfile.write(f'Number of blocks,{num_blocks}\n')
        csvfile.write(f'Main chain length,{main_chain_length}\n')
        csvfile.write(f'Fraction of main blocks,{float(main_chain_length)/num_blocks}\n')

        csvfile.write(f'Number of orphan blocks,{num_orphan_blocks}\n')
        csvfile.write(f'Fraction of orphan blocks,{float(num_orphan_blocks)/num_blocks}\n')

        if params['fork_choice_rule']=='longest-chain' or params['fork_choice_rule']=='GHOST':
            csvfile.write(f'Expected fraction of main blocks,{1.0/(1+f*delta_blocks)}')
            csvfile.write(f'Expected fraction of orphan blocks,{float(f*delta_blocks)/(1+f*delta_blocks)}\n')
            csvfile.write(f'Expected arrival rate,{float(f)/(1+f*delta_blocks)}\n')
            csvfile.write(f'Expected arrival latency,{1/(float(f)/(1+f*delta_blocks))}\n')
            csvfile.write(f'Expected finalization latency,{finalization_depth * float(1+f*delta_blocks)/f}\n')

def draw_blocktree(params, proposals, main_chain):
    g = Graph()
    color_vp = g.new_vertex_property('double')
    shape_vp = g.new_vertex_property('int')
    text_vp = g.new_vertex_property('string')

    # maps vertex to block
    vertex_to_blocks = g.new_vertex_property('object')
    # maps block to vertex
    block_to_vertices = {}

    added_edges = 0
    # add all vertices
    for block in main_chain:
        v = g.add_vertex()
        color_vp[v] = 1
        shape_vp[v] = 1
        text_vp[v] = block.id
        block_to_vertices[block.id] = v

    # add all edges
    for block in main_chain:
        child_vertex = block_to_vertices[block.id]
        if block.parent_id!=None:
            if block.parent_id not in block_to_vertices:
                parent_vertex = g.add_vertex()
                color_vp[parent_vertex] = 1
                shape_vp[parent_vertex] = 1
                text_vp[parent_vertex] = block.parent_id
                block_to_vertices[block.parent_id] = parent_vertex
            else:
                parent_vertex = block_to_vertices[block.parent_id]
            g.add_edge(child_vertex, parent_vertex) 
        # if a block has referenced blocks, add them
        if hasattr(block, 'referenced_blocks'):
            for ref_block in block.referenced_blocks:
                ref_vertex = g.add_vertex()
                color_vp[ref_vertex] = 0.5
                shape_vp[ref_vertex] = 0.5
                text_vp[ref_vertex] = ref_block.id
                g.add_edge(ref_vertex, child_vertex)
                block_to_vertices[ref_block.id] = ref_vertex

    pos = fruchterman_reingold_layout(g, n_iter=1)

    graph_draw(g,
            vertex_size=50,
            vertex_text=text_vp,
            vertex_shape=shape_vp,
            vertex_fill_color =color_vp,
            vertex_font_size=15, output_size=(4200, 4200),
            edge_pen_width=1.0,
            output="./logs/blocktree.png")

