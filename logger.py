import csv
from graph_tool.all import *
from network import constant_decker_wattenhorf
from constants import TX_SIZE

def log_global_blocktree(global_blocktree):
    with open('./logs/global_blocktree.log', 'w+') as f:
        f.write(f'{global_blocktree.graph_to_str()}') 

    with open('./logs/blocks.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'Parent id', 'Transactions']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for block in global_blocktree.blocks:
            tx_str = ';'.join(tx.id for tx in block.txs)
            writer.writerow({'id': f'{block.id}', 'Parent id':
                f'{block.parent_id}', 'Transactions': f'{tx_str}'})

def log_txs(txs):
    with open('./logs/transactions.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'Source Node', 'Arrival Timestamp', 'Main Chain Arrival Timestamp', 'Finalization Timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for tx in txs:
            writer.writerow({'id': f'{tx.id}', 'Source Node':
                f'{tx.source.node_id}', 'Arrival Timestamp':
                f'{tx.timestamp}', 'Main Chain Arrival Timestamp':
                f'{tx.main_chain_timestamp}', 'Finalization Timestamp':
                f'{tx.finalization_timestamp}'})

def log_proposals(proposals):
    with open('./logs/proposals.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'Timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for p in proposals:
            writer.writerow({'id': f'{p.id}', 'Timestamp': f'{p.timestamp}'})

def log_statistics(params):
    with open('./logs/stats.log', 'w+') as f:
        if params['model']=='Decker-Wattenhorf' or params['model']=='Constant-Decker-Wattenhorf':
            f.write(f'Average network latency for blocks: {constant_decker_wattenhorf(params["max_block_size"])} sec\n')
            f.write(f'Average network latency for txs: {constant_decker_wattenhorf(TX_SIZE)} sec\n')

def draw_global_blocktree(global_blocktree):
    main_chain_vp = global_blocktree.tree.new_vertex_property('int')

    # color main chain a different color
    for v in global_blocktree.main_chain():
        main_chain_vp[global_blocktree.tree.vertex(v)] = 1

    graph_draw(global_blocktree.tree,
            vertex_text=global_blocktree.tree.vertex_index,
            vertex_size=50,
            vertex_fill_color = main_chain_vp,
            vertex_font_size=15, output_size=(4200, 4200),
            edge_pen_width=1.0,
            output="./logs/global-blocktree.png")
