
import blockchain

from time import time
import Crypto
from Crypto.Hash import SHA


BLOCK_SIZE = 5 

class Block:
	def __init__(self, previousHash, nonce):
		##set

		self.previousHash = previousHash
		self.timestamp = time() 
		self.size = BLOCK_SIZE  #Mallon xreiazetai??
		self.hash = myHash() 
		print("My Hash is:")
		print(self.hash)
		print("\n")
		self.nonce = nonce 
		self.listOfTransactions = []
	
	def myHash(self):
		return SHA.new((str(self.timestamp)).encode('utf8') + (str(self.previousHash)).encode('utf8')) 


	#def add_transaction(transaction transaction, blockchain blockchain):
		#add a transaction to the block

Block(1,1)