from block import Block, Blockchain
from wallet import Wallet
from transaction import Transaction
import threading
import requests
import binascii
from headers import *

from collections import OrderedDict

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import PKCS1_v1_5

#bid = 1
#bid_lock = threading.Lock()

class Node:
	def __init__(self,ip, port, index=None, chain=None):
		self.NBC=100  
		self.index =index
		if(index==0):
			self.chain = Blockchain(index) 
			self.current_id_count=self.index+1

		else: 
			self.chain = chain 
		
		
		#self.NBCs
		self.ip = ip
		self.port = port
		self.wallet = None
		self.ring = [] 
		
	def __str__(self):
		return "My id:" + str(self.index)

#here we store information for every node, as its id, its address (ip:port) its public key and its balance 


	def next_bid():
		global bid
		with bid_lock:
			result = bid
			bid += 1
		return result

	#def.create_new_block():

	def create_wallet(self, public_key=None, private_key=None):
		if (public_key == None and private_key == None) :
			return Wallet()
		return Wallet(public_key, private_key)
			
		#create a wallet for this node, with a public key and a private key

	#def register_node_to_ring():
		#add this node to the ring, only the bootstrap node can add a node to the ring after checking his wallet and ip:port address
		#bottstrap node informs all other nodes and gives the request node an id and 100 NBCs


	def create_transaction(self, sender, receiver, amount):
		transaction = Transaction(sender_address=sender, recipient_address=receiver, amount=amount, sender_private_key=self.wallet.private_key)
		signature = transaction.sign_transaction()
		return {'transaction': transaction.to_dict(), 'signature': signature}
		#remember to broadcast it


	def broadcast_transaction(self, transaction, signature):
		for node in self.ring:
			response = requests.post('http://' + HOST + ':' + node['port'] + '/validate_transaction', json={'transaction':transaction, 'signature': signature})
			if(response.status_code != 200):
				return -1
		return 0
		
#str(self.to_dict()).encode('utf8')

	def validate_transaction(self, transaction_json):
		#use of signature and NBCs balance
		
		signature=transaction_json['signature']
		transaction=transaction_json['transaction']
		transaction=OrderedDict(transaction)
		sender_public_key=RSA.importKey(binascii.unhexlify(transaction['sender_address']))
		verifier = PKCS1_v1_5.new(sender_public_key)	
		message = str(transaction).encode('utf8')		
		h=SHA.new(message)
		
		if verifier.verify(h, binascii.unhexlify(signature)):
			print("Cool verification")
			return 0 #Den elenxo NBCs tou sender
		else:
			print("Verification Failed")
			return -1

	def add_transaction_to_block(self, transaction):
		unconfirmed_transactions= self.chain.unconfirmed_transactions
		if(len(unconfirmed_transactions)<BLOCK_SIZE):
			self.chain.unconfirmed_transactions.append(transaction)
			return 0
		else:
			#mine
			#create new block and add
			return 0
			
		#if enough transactions  mine



	def mine_block(block, blockchain):
		block.nonce = 0
		while not valid_proof(block):
			block.nonce +=1
	
		block.previous_hash = self.last_block.hash
		



	#def broadcast_block():


		

	def valid_proof(block, difficulty=MINING_DIFFICULTY):
		computed_hash = block.compute_hash()
		return computed_hash.startswith('0' * difficulty)
			




	#concencus functions

	#def valid_chain(self, chain):
		#check for the longer chain accroose all nodes


	#def resolve_conflicts(self):
		#resolve correct chain



