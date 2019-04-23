# blockchain-simulator
An experimental blockchain simulator written in python. Current algorithms available for testing are the Longest Chain Protocol and GHOST.

## Requirements
- [Python 3](https://docs.python.org/3/)
- [graph-tool](https://graph-tool.skewed.de/) 

## Description

### Parameters:
- Number of nodes (Note: current network model has all nodes connected to one another)
- Number of adversaries
- Maximum number of transactions per block
- Transaction error probability
- Fork choice rule
  - Longest chain protocol - add block to longest current chain
  - GHOST protocol - add block to heaviest subtree
- Block proposal rate
- Transaction dataset
- Poisson - a transaction occurs based on poisson distribution with rate 1 transaction/second
- Deterministic - a transaction happens at fixed timestamps
- Transaction scheduling rule
- FIFO
- Network model
    - Decker-Wattenhorf - based on “Information Propagation in Bitcoin Network” (https://ieeexplore.ieee.org/document/6688704/), we determine that the delay should be approximately 19/600 sec/tx * txs + 1 sec. Then, we use this delay as the parameter for an exponential distribution (https://docs.scipy.org/doc/numpy/reference/generated/numpy.random.exponential.html)
    - Constant Decker-Wattenhorf - for testing purposes. Same as above without randomness of exponential distribution
- Duration of simulation in seconds
- Logging - enable or disable logging

### Overall Flow of Simulation
- 1) Create nodes
- 2) Generate transaction dataset
- 3) Generate proposal events
- 4) Run simulation until all proposals and transactions exhausted. 
  - Check for next event in simulation (proposal or transaction)
  - If transaction:
    - Source node broadcasts transaction to all neighboring nodes with factored delay. Neighboring nodes add to their ‘buffer’
  - If proposal:
    - Choose random node
    - Random node creates a proposal
    - Node processes its buffer by adding received transactions into its local queue and adding received proposals into its local blocktree
    - Create a new block limited by number of transactions per block or timestamp
    - Broadcast created proposal to rest of network
- 6) Compute metrics and log results
- 7) Metrics are computed: main chain arrival timestamp, finalization timestamp
    - Main chain arrival timestamp: The main chain consists of blocks common to ALL nodes in the network. When a block on the main chain is proposed, all the tx’s in that block ‘arrive’
    - Finalization timestamp: When a block is proposed and ends up on the main chain, the block k blocks above is finalized. The parameter k is a function of the number of adversaries and the number of nodes

### Logged Results

#### Blocks.csv
- Block id
- Block parent id
- Proposal timestamp - when the block was initially proposed
- Finalization timestamp - when the block was finalized on global blocktree
- Depth - the block’s depth along the main chain
- Finalized - whether or not the block was finalized
- Transactions - ids of all transactions in the block

#### Stats.csv
- All the parameters
- Time elapsed (real time, NOT simulation time)
- Network latencies for blocks and transactions
- Finalization depth
- Number of blocks
- Length of main chain
- Fraction of main blocks
- Expected fraction of main blocks computed according to 1.0/(1+proposal_rate*block_delay)
- Fraction of orphan blocks
- Expected fraction of main blocks computed according to 1-1.0/(1+proposal_rate*block_delay)
- Expected arrival rate of blocks onto main chain
- Expected finalization latency of a block

#### Transactions.csv
- Id
- Source node
- Generated timestamp
- Main chain arrival timestamp (on global blocktree)
- Finalization timestamp (on global blocktree)

#### Blocktree.png
  Visualization of longest chain of blocktree’s main chain


