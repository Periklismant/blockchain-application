from time import time
from collections import OrderedDict
import Crypto
from Crypto.Hash import SHA
from hashlib import sha256
import json
from headers import *
from transaction import Transaction

class Blockchain:
	def __init__(self, index, unconfirmed_transactions=[], chain=[]):
		self.unconfirmed_transactions = unconfirmed_transactions
		self.chain = chain
		if (index == 0):
			self.create_genesis_block()
	
	def create_genesis_block(self):
		first_trans = Transaction('0', None, '5000', 100*NUM_OF_NODES)
		genesis_block = Block(0,[first_trans.to_dict()],"1",size=1)
		self.chain.append(genesis_block.to_dict_hash())
	
	def to_dict(self):
		return OrderedDict({'unconfirmed_transactions': self.unconfirmed_transactions, 'chain': self.chain})

	def __str__(self):
		return 'Unconf = ' + str(self.unconfirmed_transactions) + '\n' + 'chain = ' + str(self.chain)


class Block:
	def __init__(self, index, transactions, previousHash, size=BLOCK_SIZE, nonce=0):   #, nonce):
		##set
		self.index = index
		self.previousHash = previousHash
		self.timestamp = time() 
		self.size = size  
		self.nonce = nonce 
		self.transactions = transactions
		self.hash = self.compute_hash()
	
	def to_dict(self):
		return OrderedDict({'index': self.index,
				    'previousHash': self.previousHash,
				    'timestamp': self.timestamp,
				    'size': self.size,
				    'nonce': self.nonce,
				    'transactions': self.transactions})
	
	def compute_hash(self):
		block_string = json.dumps(self.to_dict(), sort_keys=True)
		return sha256(block_string.encode()).hexdigest()

	def to_dict_hash(self):
		return OrderedDict({'index': self.index,
				    'previousHash': self.previousHash,
				    'timestamp': self.timestamp,
				    'size': self.size,
				    'nonce': self.nonce,
				    'transactions': self.transactions,
				    'hash': self.hash})

	#def add_transaction(transaction transaction, blockchain blockchain):
		#add a transaction to the block


