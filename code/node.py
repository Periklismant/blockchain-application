from block import Block, Blockchain
from wallet import Wallet
from transaction import Transaction
import threading
import requests
from requests_futures.sessions import FuturesSession
import binascii
from headers import *
import json

from collections import OrderedDict

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from hashlib import sha256
from time import time

import Crypto
from Crypto.Hash import SHA256

class Node:
	def __init__(self,ip, port, index=None, chain=None): 
		self.index =index
		if(index==0):
			self.chain = Blockchain(index) 
			self.current_id_count=self.index+1

		else: 
			self.chain = chain 
		
		
		self.NBCs=[]
		self.ip = ip
		self.port = port
		self.busy = False
		self.wallet = None
		self.ring = [] 
		
	def __str__(self):
		return "My id:" + str(self.index)

#here we store information for every node, as its id, its address (ip:port) its public key and its balance 

	def get_next_in_ring(self, index):
		rlen = len(self.ring)
		if(index+1 == rlen):
			return self.ring[0]
		else:
			return self.ring[index+1]

	def create_new_block(self, transactions):
		index = len(self.chain.chain)
		previousHash = self.chain.chain[-1]['hash']
		new_block = Block(index, transactions, previousHash)
		return new_block.to_dict_hash()

	def create_wallet(self, public_key=None, private_key=None):
		if (public_key == None and private_key == None) :
			return Wallet()
		return Wallet(public_key, private_key)
			
		#create a wallet for this node, with a public key and a private key

	def balance(self):
		cash=0
		for output in self.NBCs:
			cash+=output['amount']
		return cash

	#def register_node_to_ring():
		#add this node to the ring, only the bootstrap node can add a node to the ring after checking his wallet and ip:port address
		#bottstrap node informs all other nodes and gives the request node an id and 100 NBCs


	def create_transaction(self, sender, receiver, amount, transaction_inputs):
		transaction = Transaction(sender_address=sender, recipient_address=receiver, amount=amount, sender_private_key=self.wallet.private_key, transaction_inputs=transaction_inputs)
		signature = transaction.sign_transaction()
		return {'transaction': transaction.to_dict(), 'signature': signature, 'outputs': transaction.transaction_outputs}
		#remember to broadcast it


	def broadcast_transaction(self, transaction, signature, outputs):
		session = FuturesSession()
		future = []
		for node in self.ring:
			if node['id'] != self.index:
				future.append({'resp': session.post('http://' + node['ip'] + ':' + node['port'] + '/validate_transaction', 
										json={'transaction':transaction, 'signature': signature, 'outputs': outputs},
										hooks={'response': self.response_hook}), 'ip': node['ip'], 'port': node['port']})
		retry=True
		while retry:
			retry=False 
			future_next=[]
			for fut in future:
				response = fut['resp'].result()
				if response.status_code == 503:
					ip=fut['ip']
					port=fut['port']
					future_next.append({'resp': session.post('http://' + ip + ':' + port + '/validate_transaction', 
										json={'transaction':transaction, 'signature': signature, 'outputs': outputs},
										hooks={'response': self.response_hook}), 'ip': ip, 'port': port})
					retry=True
				elif response.status_code != 200:
					return -1
			future=future_next
		return 0

	#def broadcast_validate(self, transaction, signature, outputs):
	#	session = FuturesSession()
	#	future = []
	#	for node in self.ring:
	#		if node['id'] != self.index:
	#			future.append({'resp': session.post('http://' + node['ip'] + ':' + node['port'] + '/validate_transaction', 
	#									json={'transaction':transaction, 'signature': signature, 'outputs': outputs},
	#									hooks={'response': self.response_hook}), 'ip': node['ip'], 'port': node['port']})
	#	retry=True
	#	while retry:
	#		retry=False 
	#		future_next=[]
	#		for fut in future:
	#			response = fut['resp'].result()
	#			if response.status_code == 503:
	#				ip=fut['ip']
	#				port=fut['port']
	#				future_next.append({'resp': session.post('http://' + ip + ':' + port + '/validate_transaction', 
	#									json={'transaction':transaction, 'signature': signature, 'outputs': outputs},
	#									hooks={'response': self.response_hook}), 'ip': ip, 'port': port})
	#				retry=True
	#			elif response.status_code != 200:
	#				return -1
	#		future=future_next
	#	return 0

		
#str(self.to_dict()).encode('utf8')

	def validate_transaction(self, transaction_json):
		#use of signature and NBCs balance
		#self.busy=True
		signature=transaction_json['signature']
		trans=transaction_json['transaction']
		outputs= transaction_json['outputs']
		transaction = OrderedDict()
		transaction['amount'] = trans['amount']
		transaction['sender_address'] = trans['sender_address']
		transaction['recipient_address'] = trans['recipient_address']
		#print("Validating this: ")
		#print(transaction)
		sender_public_key=RSA.importKey(binascii.unhexlify(transaction['sender_address']))
		verifier = PKCS1_v1_5.new(sender_public_key)	
		message = str(transaction).encode('utf8')		
		h=SHA.new(message)
		
		if verifier.verify(h, binascii.unhexlify(signature)):
			if outputs['sender']['amount'] >= 0:
				print("Cool verification")
				self.add_transaction_to_block(transaction_json)
				#self.busy=False
				return 0 
			else:
				print("Not enough money")
				#self.busy=False
				return -2
		else:
			print("Verification Failed")
			return -1

	def add_transaction_to_block(self, transaction):
		if(self.chain.unconfirmed_transactions):
			unconfirmed_transactions= self.chain.unconfirmed_transactions
		else:
			unconfirmed_transactions=[]
		#if(len(unconfirmed_transactions)<BLOCK_SIZE):
		self.chain.unconfirmed_transactions.append(transaction)
		print("Last block transactions count: ")
		print(len(self.chain.unconfirmed_transactions))
		print("My last transactions")
		#print(self.chain.unconfirmed_transactions)
		return 0
		#else:
		#	print("About to Mine :-)")
		#	new_block= self.create_new_block(self.chain.unconfirmed_transactions)
		#	mined_block = self.mine_block(new_block)
		#	if(mined_block == 0):
		#		return 0
		#	if(self.broadcast_block(mined_block, transaction)!=0):
		#		return -1
		#	return 0
			
		#if enough transactions  mine
	def broadcast_mine_block(self, unconfirmed_transactions):
		session = FuturesSession()
		future = []
		for node in self.ring:
			if node['id']!= self.index:
				future.append({'resp': session.post('http://' + node['ip'] + ':' + node['port'] + '/mine', 
										json=unconfirmed_transactions,
										hooks={'response': self.response_hook}), 'ip': node['ip'], 'port': node['port']})
		retry=True
		while retry:
			retry=False 
			future_next=[]
			for fut in future:
				response = fut['resp'].result()
				if response.status_code == 503:
					ip=fut['ip']
					port=fut['port']
					future_next.append({'resp': session.post('http://' + ip + ':' + port + '/mine', 
										json=unconfirmed_transactions,
										hooks={'response': self.response_hook}), 'ip': ip, 'port': port})
					retry=True
				elif response.status_code != 200:
					return -1
			future=future_next
		return 0
	def mine_block(self, block):
		myhash = block['hash']
		del block['hash']
		block['nonce'] = 0
		while ((not self.valid_proof(myhash))):
			block['nonce'] +=1
			block_string = json.dumps(block, sort_keys=True)
			myhash = sha256(block_string.encode()).hexdigest()
			if len(self.chain.chain) != block['index']:
				return 0
		block['hash']=myhash
		print("I MINED THE NEXT BLOCK :-D")
		#print(block)
		return block

	def response_hook(resp, *args, **kwargs):
		resp.data = resp


	def broadcast_block(self, mined_block):
		session = FuturesSession()
		future = []
		for node in self.ring:
			if node['id'] != self.index:
				future.append({'resp': session.post('http://' + node['ip'] + ':' + node['port'] + '/get_mined_block', 
										json={'block': mined_block}, 
										hooks={'response': self.response_hook}),'ip': node['ip'], 'port': node['port']})
		retry=True
		while retry:
			retry=False
			future_next=[]
			for fut in future:
				response = fut['resp'].result()
				if response.status_code == 503:
					ip=fut['ip']
					port=fut['port']
					future_next.append({'resp': session.post('http://' + ip + ':' + port + '/get_mined_block', 
										json={'block': mined_block}, 
										hooks={'response': self.response_hook}), 'ip': ip, 'port': port})
					retry=True
				elif response.status_code != 200:
					return -1
			future=future_next
		return 0

		

	def valid_proof(self, myhash, difficulty=MINING_DIFFICULTY):
		return myhash.startswith('0' * difficulty)
			
	#concencus functions

	def valid_chain(self, chain=None):
		if chain == None:
			chain = self.chain.chain
		last_block = chain[-1]
		i = 1
		while i < len(chain):
			blockprev = chain[i-1].copy()
			block = chain[i].copy()
			if block['previousHash'] != blockprev['hash']:
				print("Chain previous hash error!")
				new_chain = self.resolve_conflicts()
				if(new_chain != None):
					print("Conflict resolved :-)")
					return True
				else:
					print("Chain still has a problem")
					return False
			block_hash = block.pop('hash', None)
			block_string = json.dumps(block, sort_keys=True)
			myhash = sha256(block_string.encode()).hexdigest()
			if(not self.valid_proof(myhash)):
				print("Block not hashed correctly!")
				return False
			block['hash'] = myhash
			i+=1
		print("Chain is valid! :-)")
		return True

	def resolve_conflicts(self):
		my_chain = self.chain.chain
		new_chain = None
		max_length = len(my_chain)
	
		session = FuturesSession()
		future = []
		for node in self.ring:
			if node['id'] != self.index:
				future.append({'resp': session.get('http://' + node['ip'] + ':' + node['port'] + '/get_chain', hooks={'response': self.response_hook}), 'ip': node['ip'], 'port': node['port']})
		retry=True
		while retry:
			retry=False
			future_next=[]
			for fut in future:
				response = fut['resp'].result()
				if response.status_code == 503:
					ip=fut['ip']
					port=fut['port']
					future_next.append({'resp': session.get('http://' + ip + ':' + port + '/get_chain', hooks={'response': self.response_hook}), 'ip': ip, 'port': port})
					retry =True
				elif(response.status_code != 200):
					return -1
				else:
					length = response.json()['length']
					chain = response.json()['chain']
					if length > max_length and self.valid_chain(chain):
						max_length=length
						new_chain=chain
			future=future_next
		if new_chain:
			self.chain = new_chain
		
		return new_chain