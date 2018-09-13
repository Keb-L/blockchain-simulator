import csv
from graph_tool.all import *
from network import constant_decker_wattenhorf
from constants import TX_SIZE

def log_local_blocktree(node):
    with open(f'./logs/{node.node_id}.log', 'w+') as f:
        f.write(f'{node.local_blocktree.graph_to_str()}') 

    with open(f'./logs/{node.node_id}.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'Transactions']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for vertex in node.local_blocktree.main_chain():
            block = node.local_blocktree.vertex_to_blocks[vertex]
            tx_str = ';'.join(tx.id for tx in block.txs)
            writer.writerow({'id': f'{block.id}', 'Transactions': f'{tx_str}'})

def log_global_blocktree(global_blocktree):
    with open('./logs/global_blocktree.log', 'w+') as f:
        f.write(f'{global_blocktree.graph_to_str()}') 

    with open('./logs/blocks.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'Parent id', 'Proposal timestamp', 
                'Finalization timestamp', 'Depth', 'Finalized', 'Transactions']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for block in global_blocktree.vertex_to_blocks:
            vertex = global_blocktree.block_to_vertices[block.id] 
            tx_str = ';'.join(tx.id for tx in block.txs)
            depth = global_blocktree.depth[vertex]
            is_finalized = False if block.finalization_timestamp==None else True
            writer.writerow({'id': f'{block.id}', 'Parent id':
                f'{block.parent_id}', 'Proposal timestamp':
                f'{block.proposal_timestamp}', 'Finalization timestamp':
                f'{block.finalization_timestamp}', 'Depth': f'{depth}',
                'Finalized': f'{is_finalized}', 'Transactions': f'{tx_str}'})

def log_txs(txs):
    with open('./logs/transactions.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'Source Node', 'Arrival Timestamp', 
                'Main Chain Arrival Timestamp', 
                'Finalization Timestamp', 'Optimistic Confirmation Time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for tx in txs:
            writer.writerow({'id': f'{tx.id}', 'Source Node':
                f'{tx.source.node_id}', 'Arrival Timestamp':
                f'{tx.timestamp}', 'Main Chain Arrival Timestamp':
                f'{tx.main_chain_timestamp}', 'Finalization Timestamp':
                f'{tx.finalization_timestamp}', 'Optimistic Confirmation Time':
                f'{tx.optimistic_confirmation_time}'})

def log_statistics(params, global_blocktree):
    with open('./logs/stats.csv', 'w+') as csvfile:
        delta_blocks = constant_decker_wattenhorf(params["max_block_size"])
        delta_txs = constant_decker_wattenhorf(TX_SIZE)
        f = params["proposal_rate"]
        # log network latency information
        if params['model']=='Decker-Wattenhorf' or params['model']=='Constant-Decker-Wattenhorf':
            csvfile.write(f'Average network latency for blocks (sec),{delta_blocks}\n')
            csvfile.write(f'Average network latency for txs (sec),{delta_txs}\n')

        # log finalization depth
        finalization_depth = global_blocktree.compute_k(params['tx_error_prob'], params['num_nodes'], params['num_adversaries'])
        csvfile.write(f'Finalization depth,{finalization_depth}\n')

        # log main chain information blocks
        num_blocks = len(global_blocktree.tree.get_vertices())
        main_chain_length = len(global_blocktree.main_chain())
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
    main_chain_vp = global_blocktree.tree.new_vertex_property('int')

    # color main chain a different color
    for v in global_blocktree.main_chain():
        main_chain_vp[global_blocktree.tree.vertex(v)] = 1

    pos = radial_tree_layout(global_blocktree.tree, global_blocktree.tree.vertex(0))

    graph_draw(global_blocktree.tree,
            pos = pos,
            vertex_text=global_blocktree.tree.vertex_index,
            vertex_size=50,
            vertex_fill_color = main_chain_vp,
            vertex_font_size=15, output_size=(4200, 4200),
            edge_pen_width=1.0,
            output="./logs/global-blocktree.png")
