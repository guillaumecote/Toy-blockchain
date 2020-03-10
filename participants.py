from ecdsa.curves import SECP256k1
from ecdsa import SigningKey, VerifyingKey
from hashlib import sha256
from blockchain import Blockchain, Block, Transaction
import time
import math
import json


class User():
    def __init__(self, chain_id):
        self.blockchain = Blockchain(chain_id)
        self.generate_account()

    def generate_account(self):
        self.private_key = SigningKey.generate(curve=SECP256k1, hashfunc = sha256)
        self.public_key = self.private_key.get_verifying_key()
        self.address = sha256(self.public_key.to_string()).hexdigest()

    def sign_tx(self, tx):
        sig = self.private_key.sign(bytes.fromhex(tx.hash))
        tx.signature = sig.hex()

    def submit_transaction(self, to_address, amount, fee):
        tx = Transaction(self.address, to_address, amount, fee)
        self.sign_tx(tx)

        print('Submitting transaction - User {}'.format(self.address[:4]))
        tx.display()
        self.blockchain.submit_transaction(tx)

    def get_balance(self):
        self.blockchain.update_data()
        return self.blockchain.get_balance(self.address)


class Miner(User):
    def __init__(self, chain_id):
        super().__init__(chain_id)

    def mine_continuously(self):
        while True:
            self.mine_one_block()

    def mine_one_block(self):
        self.blockchain.update_data()
        block = self.make_next_block()
        height = self.blockchain.height()
        lastcheck = time.time()
        while block.compute_hash()[:block.difficulty] != '0'* block.difficulty:
            if time.time() - lastcheck > 1:
                if height != self.blockchain.height():
                    break
                else:
                    lastcheck = time.time()
            block.nonce = block.nonce+1
        if height != self.blockchain.height():
            print('Someone already mined block #{}'.format(height+1))
        else:
            block.hash = block.compute_hash()
            print('Successfully mined block - Miner {}'.format(self.address[:4]))
            block.display()
            self.blockchain.submit_block(block)

    def make_next_block(self):
        if not self.blockchain.blocks:
            new_block = Block(time.time(), [Transaction(None, self.address, self.blockchain.mining_reward, 0)], 'Genesis', 1)
        else:
            txs = []
            invalid_txs = []

            highest_fee_txs = sorted(self.blockchain.mempool, key=lambda x: x.fee, reverse = True)
            included_amount = {}
            for tx in highest_fee_txs:
                if tx.from_address not in included_amount:
                    included_amount[tx.from_address] = 0
                if tx.amount + tx.fee<= self.blockchain.get_balance(tx.from_address) - included_amount[tx.from_address]:
                    txs.append(tx)
                    included_amount[tx.from_address] += tx.amount+tx.fee
                    if len(txs) >= self.blockchain.MAX_TX_PER_BLOCK - 1:
                        break
                else:
                    invalid_txs.append(tx)
            if invalid_txs:
                self.blockchain.mempool = [tx for tx in self.blockchain.mempool if tx not in invalid_txs]
                self.blockchain.save_data(self.blockchain.mempool, 'mempool')
            total_fees = sum([tx.fee for tx in txs])
            txs.append(Transaction(None, self.address, self.blockchain.mining_reward + total_fees, 0))
            timestamp = time.time()
            new_block = Block(timestamp, txs, self.blockchain.blocks[-1].hash, self.calculate_difficulty(timestamp))
        return new_block

    def calculate_difficulty(self, timestamp):
        if (self.blockchain.height() + 1) % self.blockchain.DIFF_ADJUSTMENT_RATE == 0:
            difficulty = min(math.ceil(self.blockchain.DIFF_ADJUSTMENT_RATE* self.blockchain.TARGET_TIME_PER_BLOCK/(timestamp - self.blockchain.blocks[1-self.blockchain.DIFF_ADJUSTMENT_RATE].timestamp)), self.blockchain.MAX_DIFFICULTY)
            print('Changed difficulty to {}'.format(difficulty))
        else:
            difficulty = self.blockchain.blocks[-1].difficulty
        return difficulty
