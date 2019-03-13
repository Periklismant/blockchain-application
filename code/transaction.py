from collections import OrderedDict

import binascii

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from hashlib import sha256
from time import time

import Crypto
from Crypto.Hash import SHA256

import uuid
import json
import requests
from flask import Flask, jsonify, request, render_template
from headers import *

class Transaction:

	def __init__(self, sender_address, sender_private_key, recipient_address, amount):

	        self.sender_address = sender_address
	        self.sender_private_key = sender_private_key
	        self.recipient_address = recipient_address
	        self.amount = amount
      
		#self.transaction_inputs: 
	        #self.transaction_outputs: 
        	#self.signature = sign_transaction()
		#self.transaction_id = myHash()
 
	def compute_hash(self):
		transaction_string = json.dumps(self.to_dict(), sort_keys=True)
		self.hash = sha256(transaction_string.encode()).hexdigest()		
		return self.hash


	def __getattr__(self, attr):
		return self.data[attr]

	def to_dict(self):
		return OrderedDict({'sender_address': self.sender_address,
		                    'recipient_address': self.recipient_address,
		                    'amount': self.amount})
	def to_dict_signed(self):
		return OrderedDict({'sender_address': self.sender_address,
		                    'recipient_address': self.recipient_address,
		                    'amount': self.amount,
				    'signature': self.signature})

	def sign_transaction(self):
		"""
		Sign transaction with private key
		"""
		private_key = RSA.importKey(binascii.unhexlify(self.sender_private_key))
		signer = PKCS1_v1_5.new(private_key)
		message = str(self.to_dict()).encode('utf8')
		h = SHA.new(message)
		signature= binascii.hexlify(signer.sign(h)).decode('ascii')
		return signature

	# def sign_transaction(self):
	    #    signer = PKCS1_v1_5.new(sender_private_key)
	    #    digest = SHA.new(self.transaction_id)
	    #    return signer.sign(digest)

Transaction(1, 2525, 2, 50)
