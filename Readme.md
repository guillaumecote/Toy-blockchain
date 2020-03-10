Toy blockchain, mainly for educational purposes, built in python.

It's a database stored locally that mimics, in a limited way, many of the features present in a payment system such as Bitcoin. 

In its current form, it includes:

- Chained blocks with hash pointers
- Blockchain validity checks (Valid pointers, signature, transaction amounts, balance checks, difficulty level, etc..)
- Proof of Work (POW)
- Adjustable POW difficulty
- Miner rewards
- User ID (private key, public key and address)
- Transactions and transaction signing
- Fees/Miner fee-based transaction selection
- A mempool

How to:
Multiple Miner() and User() instances can be created. A blockchain id is required to select which blockchain the miner/user wants to act on. New submitted transactions are saved in the mempool file in the storage folder. Miners can call mine_one_block() to create/mine the next block. When successful, they receive a mining reward. 



To-do:
- Simulation with multiple users/miners doing work in parallel
- Limit memory usage
- Make updating blockchain data into a core-routine to ensure up-to-date data for every function call
- Smart fee market in simulation
- Make valid "longest chain" fork selection for miners
- ...?
