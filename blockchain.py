import time
import hashlib
import json
import pickle
import os
import math


class Blockchain():
    MAX_TX_PER_BLOCK = 5 # Includes mining reward
    TARGET_TIME_PER_BLOCK = 10
    DIFF_ADJUSTMENT_RATE = 5 #Diff adjusted every 5 blocks
    MAX_DIFFICULTY = 4 # Because who is mining anyway?
    def __init__(self, id = ''):
        self.version = id
        self.update_data()
        self.difficulty = 2
        self.mining_reward = 100

    def update_data(self):
        self.blocks = self.load_data('blockchain')
        self.mempool = self.load_data('mempool')


    def load_data(self, type):
        fname = 'storage/{}_v{}.pickle'.format(type, self.version)
        if os.path.isfile(fname):
            with open(fname, 'rb') as f:
                blockchain = pickle.load(f)
            if blockchain:
                return blockchain
        return []

    def save_data(self, data, type):
        fname = 'storage/{}_v{}.pickle'.format(type, self.version)
        with open(fname, 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


    def submit_block(self, block):
        if self.verify_block(block):
            self.mempool = [tx for tx in self.mempool if tx not in block.transactions]
            self.blocks.append(block)

            self.save_data(self.mempool, 'mempool')
            self.save_data(self.blocks, 'blockchain')


    def submit_transaction(self, transaction):
        self.mempool.append(transaction)
        self.save_data(self.mempool, 'mempool')

    def is_valid(self):
        for i, block in enumerate(self.blocks[1:], 1):
            if block.previous_hash != self.blocks[i-1].hash:
                print('Chain invalid')
                print("Block #{}'s 'previous hash' doesn't match #{}'s hash".format(i, i-1))
                print(block.previous_hash, self.blocks[i-1].hash)
                return False
            if block.hash != block.compute_hash():
                print('Chain invalid')
                print("Block #{}'s hash is invalid'".format(i))
                return False
            if block.difficulty != self.calculate_difficulty(i+1):
                print('Chain invalid')
                print("Block #{}'s difficulty is invalid. It's {}, but should be {}".format(i, block.difficulty, self.calculate_difficulty(i+1)))
                return False
            if len(block.transactions) > self.MAX_TX_PER_BLOCK:
                print('Chain invalid')
                print("Block #{} is invalid. {} transactions, max allowed is {}".format(i, len(block.transactions), self.MAX_TX_PER_BLOCK))
                return False

            miner_reward_txs = []
            total_fees = sum([tx.fee for tx in block.transactions])
            for j, tx in enumerate(block.transactions):
                if tx.from_address:
                    if tx.amount + tx.fee> self.get_balance(tx.from_address, i+1):
                        print('Chain invalid')
                        print("Block #{} has invalid transactions. Transaction #{} has amount + fees of {}, max allowed is {} (total balance)".format(i, j, tx.amount + tx.fee, self.get_balance(tx.from_address, i+1)))
                        return False
                else:
                    if tx.amount <= self.mining_reward + total_fees:
                        miner_reward_txs.append(tx)
                    else:
                        print('Chain invalid')
                        print("Block #{} has invalid miner's reward. Transaction #{} has a reward of {}, max allowed is {}".format(i, j, tx.amount, self.mining_reward + total_fees))
                        return False

                if not tx.valid_sig():
                    print('Chain invalid')
                    print("Block #{} has an invalid transaction. Transaction #{} has an invalid signature".format(i, j))
                    return False

            if len(miner_reward_txs) > 1:
                print('Chain invalid')
                print("Block #{} has multiple miner reward transactions".format(i))
                return False

        else:
            return True

    def calculate_difficulty(self, height):
        if height % self.DIFF_ADJUSTMENT_RATE == 0:
            difficulty = min(math.ceil(self.DIFF_ADJUSTMENT_RATE * self.TARGET_TIME_PER_BLOCK/(self.blocks[height-1].timestamp - self.blocks[height-self.DIFF_ADJUSTMENT_RATE].timestamp)), self.MAX_DIFFICULTY)
        else:
            difficulty = self.blocks[height-1].difficulty
        return difficulty

    def get_balance(self, address, height = None):
        if not height:
            height = self.height()
        balance = 0
        for block in self.blocks[:height]:
            for tx in block.transactions:
                if tx.from_address == address:
                    balance -= tx.amount
                elif tx.to_address == address:
                    balance += tx.amount
        return balance


    def verify_block(self, block):
        return True

    def height(self):
        self.update_data()
        return len(self.blocks)

class Block():
    def __init__(self, timestamp, transactions, previous_hash, difficulty):
        self.difficulty = difficulty
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = ''

    def compute_hash(self):
        data = str(self.timestamp) + json.dumps(self.transactions, default=lambda x: x.__dict__) + self.previous_hash + str(self.nonce)
        return hashlib.sha256(data.encode("utf8")).hexdigest()


    def display(self):
        print('----BLOCK----')
        print('Difficulty: {}'.format(self.difficulty))
        print('Hash: {}'.format(self.hash))
        print('Previous Hash: {}'.format(self.previous_hash))
        print('Nonce: {}'.format(self.nonce))
        print('Timestamp: {}'.format(self.timestamp))
        print('Transactions: ')
        numtx = len(self.transactions)
        for tx in self.transactions[:min(numtx,3)]:
            tx.display()
        if numtx>3:
            print('+ {} more...'.format(numtx-3))
        print('-------------')


class Transaction():
    def __init__(self, from_address, to_address, amount, fee, sig = None):
        self.from_address = from_address
        self.to_address = to_address
        self.amount = amount
        self.fee = fee
        self.hash = self.get_hash()
        self.signature = sig

    def get_hash(self):
        tx_data = str(self.from_address) + str(self.to_address) + str(self.amount)
        return sha256(tx_data.encode("utf8")).hexdigest()

    def valid_sig(self):
        keys = VerifyingKey.from_public_key_recovery(bytes.fromhex(self.signature), bytes.fromhex(self.hash), curve = SECP256k1, hashfunc = sha256)
        hash_matches =  [sha256(k.to_string()).hexdigest() == self.from_address for k in keys]
        if any(hash_matches):
            return True
        else:
            return False

    def display(self):
        print(json.dumps(self, default=lambda x: x.__dict__))
