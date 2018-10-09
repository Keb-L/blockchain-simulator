import csv, json
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

def log_global_blocktree(params, global_blocktree):
    max_block_size = params['max_block_size']

    with open('./logs/blocks.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 
                    'parent id', 
                    'proposal timestamp', 
                    'pool block timestamp', 
                    'finalization timestamp', 
                    'depth', 
                    'finalized', 
                    'emptiness',
                    'transactions']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for block in global_blocktree.vertex_to_blocks:
            vertex = global_blocktree.block_to_vertices[block.id] 
            tx_str = ';'.join(tx.id for tx in block.txs)
            depth = global_blocktree.depth[vertex]
            is_finalized = False if block.finalization_timestamp==None else True
            writer.writerow({
                'id': f'{block.id}', 
                'parent id': f'{block.parent_id}', 
                'proposal timestamp': f'{block.proposal_timestamp}', 
                'pool block timestamp': f'{block.pool_block_ref_timestamp}', 
                'finalization timestamp': f'{block.finalization_timestamp}', 
                'depth': f'{depth}',
                'finalized': f'{is_finalized}', 
                'emptiness': f'{block.emptiness}',
                'transactions': f'{tx_str}'})
            for pool_block in block.referenced_blocks:
                pool_tx_str = ';'.join(tx.id for tx in pool_block.txs)
                writer.writerow({
                    'id': f'{pool_block.id}', 
                    'parent id': f'{pool_block.parent_id}', 
                    'proposal timestamp': f'{pool_block.proposal_timestamp}', 
                    'finalization timestamp': f'{block.finalization_timestamp}', 
                    'depth': f'NA',
                    'finalized': f'{is_finalized}',
                    'emptiness': f'{pool_block.emptiness}',
                    'transactions': f'{pool_tx_str}'
                    })

def log_txs(txs):
    with open('./logs/transactions.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'source node', 'generated timestamp', 
                'pool block arrival timestamp', 'pool block reference timestamp',
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
                f'{tx.timestamp}', 'pool block arrival timestamp':
                f'{tx.pool_block_arr_timestamp}', 'pool block reference timestamp':
                f'{tx.pool_block_ref_timestamp}', 'main chain arrival timestamp':
                f'{tx.main_chain_timestamp}',
                f'finalization timestamps':
                f'{finalization_timestamp_str}'})

def log_statistics(params, global_blocktree, time_elapsed):
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

        # log finalization depth
        finalization_depth = global_blocktree.compute_k(params['tx_error_prob'], params['num_nodes'], params['num_adversaries'])
        csvfile.write(f'Finalization depth,{finalization_depth}\n')

        # log main chain information blocks
        num_blocks = 0
        for v in global_blocktree.tree.get_vertices():
            num_blocks+=(len(global_blocktree.vertex_to_blocks[v].referenced_blocks)+1)
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
    color_vp = global_blocktree.tree.new_vertex_property('double')
    shape_vp = global_blocktree.tree.new_vertex_property('int')
    text_vp = global_blocktree.tree.new_vertex_property('string')

    main_chain = global_blocktree.random_main_chain()
    main_chain_ids = list(map(lambda b: b.id, main_chain))

    for b_id in global_blocktree.block_to_vertices:
        v = global_blocktree.block_to_vertices[b_id]
        text_vp[global_blocktree.tree.vertex(v)] = b_id
        # squares for tree blocks
        shape_vp[global_blocktree.tree.vertex(v)] = 2
        if b_id in main_chain_ids:
            # yellow for main chain blocks
            color_vp[global_blocktree.tree.vertex(v)] = 0.8
        else:
            # red for orphan blocks
            color_vp[global_blocktree.tree.vertex(v)] = 0.2

    # color main chain a different color
    for b in global_blocktree.main_chains()[0]:
        if b.id in global_blocktree.block_to_vertices:
            v = global_blocktree.block_to_vertices[b.id]
            # main chain color
            color_vp[global_blocktree.tree.vertex(v)] = 1
            for pool_block in b.referenced_blocks:
                pool_vertex = global_blocktree.tree.add_vertex()
                text_vp[global_blocktree.tree.vertex(pool_vertex)] = pool_block.id
                # circles for pool blocks
                shape_vp[pool_vertex] = 0
                # blue for pool blocks
                color_vp[pool_vertex] = 0
                global_blocktree.tree.add_edge(v, pool_vertex)

    pos = radial_tree_layout(global_blocktree.tree, global_blocktree.tree.vertex(0))

    graph_draw(global_blocktree.tree,
            vertex_size=50,
            vertex_text=text_vp,
            vertex_shape=shape_vp,
            vertex_fill_color =color_vp,
            vertex_font_size=15, output_size=(4200, 4200),
            edge_pen_width=1.0,
            output="./logs/blocktree.png")
