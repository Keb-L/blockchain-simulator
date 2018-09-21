import csv
from graph_tool.all import *
from network import constant_decker_wattenhorf
from constants import TX_SIZE

def log_local_blocktree(node):
    with open(f'./logs/{node.node_id}-transactions.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'optimistic confirmation timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for vertex in node.local_blocktree.main_chains()[0]:
            block = node.local_blocktree.vertex_to_blocks[vertex]
            for tx in block.txs:
                writer.writerow({'id': f'{tx.id}', 'Optimistic confirmation timestamp':
                f'{block.optimistic_confirmation_timestamp}'})

def log_global_blocktree(global_blocktree):
    with open('./logs/global_blocktree.log', 'w+') as f:
        f.write(f'{global_blocktree.graph_to_str()}') 

    with open('./logs/blocks.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'parent id', 'proposal timestamp', 'pool block timestamp', 'finalization timestamp', 'depth', 'finalized', 'transactions']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for block in global_blocktree.vertex_to_blocks:
            vertex = global_blocktree.block_to_vertices[block.id] 
            tx_str = ';'.join(tx.id for tx in block.txs)
            depth = global_blocktree.depth[vertex]
            is_finalized = False if block.finalization_timestamp==None else True
            writer.writerow({'id': f'{block.id}', 'parent id':
                f'{block.parent_id}', 'proposal timestamp':
                f'{block.proposal_timestamp}', 'pool block timestamp':
                f'{block.pool_block_timestamp}', 'finalization timestamp':
                f'{block.finalization_timestamp}', 'depth': f'{depth}',
                'finalized': f'{is_finalized}', 'transactions': f'{tx_str}'})
            for pool_block in block.referenced_blocks:
                pool_tx_str = ';'.join(tx.id for tx in pool_block.txs)
                writer.writerow({'id': f'{pool_block.id}', 'parent id':
                    f'{pool_block.parent_id}', 'proposal timestamp':
                    f'{pool_block.proposal_timestamp}', 'finalization timestamp':
                    f'{block.finalization_timestamp}', 'depth': f'NA',
                    'finalized': f'{is_finalized}', 'transactions': f'{pool_tx_str}'})

def log_txs(txs):
    with open('./logs/transactions.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'source node', 'generated timestamp', 
                'main chain arrival timestamp', 'pool block timestamp', 
                'finalization timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for tx in txs:
            writer.writerow({'id': f'{tx.id}', 'source node':
                f'{tx.source.node_id}', 'generated timestamp':
                f'{tx.timestamp}', 'main chain arrival timestamp':
                f'{tx.main_chain_timestamp}', 'pool block timestamp':
                f'{tx.pool_block_timestamp}', 'finalization timestamp':
                f'{tx.finalization_timestamp}'})

def log_statistics(params, global_blocktree):
    with open('./logs/stats.csv', 'w+') as csvfile:
        delta_blocks = constant_decker_wattenhorf(params['max_block_size'])
        delta_txs = constant_decker_wattenhorf(TX_SIZE)
        f = params['tree_proposal_rate']
        # log network latency information
        if params['model']=='Decker-Wattenhorf' or params['model']=='Constant-Decker-Wattenhorf':
            csvfile.write(f'Average network latency for blocks (sec),{delta_blocks}\n')
            csvfile.write(f'Average network latency for txs (sec),{delta_txs}\n')

        # log finalization depth
        finalization_depth = global_blocktree.compute_k(params['tx_error_prob'], params['num_nodes'], params['num_adversaries'])
        csvfile.write(f'Finalization depth,{finalization_depth}\n')

        # log main chain information blocks
        num_blocks = len(global_blocktree.tree.get_vertices())
        main_chain_length = len(global_blocktree.main_chains()[0])
        num_orphan_blocks = num_blocks - main_chain_length 
        csvfile.write(f'Number of blocks,{num_blocks}\n')
        csvfile.write(f'Main chain length,{main_chain_length}\n')
        csvfile.write(f'Fraction of main blocks,{float(main_chain_length)/num_blocks}\n')
        csvfile.write(f'Expected fraction of main blocks,{1.0/(1+f*delta_blocks)}\n')
        csvfile.write(f'Number of orphan blocks,{num_orphan_blocks}\n')
        csvfile.write(f'Fraction of orphan blocks,{float(num_orphan_blocks)/num_blocks}\n')
        csvfile.write(f'Expected fraction of orphan blocks,{float(f*delta_blocks)/(1+f*delta_blocks)}\n')

        # log information about latencies
        csvfile.write(f'Expected arrival rate,{float(f)/(1+f*delta_blocks)}\n')
        csvfile.write(f'Expected finalization latency,{finalization_depth * float(1+f*delta_blocks)/f}\n')

def draw_global_blocktree(global_blocktree):
    main_chain_color_vp = global_blocktree.tree.new_vertex_property('int')
    main_chain_text_vp = global_blocktree.tree.new_vertex_property('string')

    # color main chain a different color
    for b in global_blocktree.main_chains()[0]:
        if b.id in global_blocktree.block_to_vertices:
            v = global_blocktree.block_to_vertices[b.id]
            main_chain_color_vp[global_blocktree.tree.vertex(v)] = 1
        main_chain_text_vp[global_blocktree.tree.vertex(v)] = b.id

    pos = radial_tree_layout(global_blocktree.tree, global_blocktree.tree.vertex(0))

    graph_draw(global_blocktree.tree,
            vertex_text= main_chain_text_vp,
            vertex_size=50,
            vertex_fill_color = main_chain_color_vp,
            vertex_font_size=15, output_size=(4200, 4200),
            edge_pen_width=1.0,
            output="./logs/global-blocktree.png")

def draw_main_chain(global_blocktree):
    main_chain = Graph()

    main_chain_shape_vp =main_chain.new_vertex_property('int')
    main_chain_text_vp =main_chain.new_vertex_property('string')

    prev_v = None

    for b in global_blocktree.main_chains()[0]:
        v = main_chain.add_vertex()
        main_chain_text_vp[main_chain.vertex(v)] = b.id
        if b.id in global_blocktree.block_to_vertices:
            main_chain_shape_vp[main_chain.vertex(v)] = 2
        else:
            main_chain_shape_vp[main_chain.vertex(v)] = 1
        if prev_v is not None:
            main_chain.add_edge(prev_v, v)
        prev_v = v

    graph_draw(main_chain,
            vertex_text = main_chain_text_vp,
            vertex_size=50,
            vertex_shape = main_chain_shape_vp,
            vertex_font_size=15, output_size=(4200, 4200),
            edge_pen_width=1.0,
            output="./logs/main-chain.png")
