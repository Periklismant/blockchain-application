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
	def __init__(self, sender_address, sender_private_key, recipient_address, amount, transaction_inputs=[]):
		self.sender_address = sender_address
		self.sender_private_key = sender_private_key
		self.recipient_address = recipient_address
		self.amount = amount
		self.transaction_inputs = transaction_inputs
		self.hash = self.compute_hash()
		self.transaction_outputs = self.compute_outputs()

	def __getattr__(self, attr):
		return self.data[attr]

	def compute_outputs(self):
		cash=0
		for inp in self.transaction_inputs:
			cash+=inp['amount']
		return {'sender': {'id': self.senderId(cash),'TransactionId': self.hash,'recipient_address': self.sender_address, 'amount':cash-self.amount}, 
				'recipient': {'id': self.recipientId(), 'TransactionId': self.hash,'recipient_address': self.recipient_address, 'amount':self.amount}}

	def senderId(self, cash):
		info_dict = OrderedDict({'TransactionId': self.hash,'recipient_address': self.sender_address, 'amount':cash-self.amount})
		sender_string = json.dumps(info_dict, sort_keys=True)
		return sha256(sender_string.encode()).hexdigest()

	def recipientId(self):
		info_dict = OrderedDict({'TransactionId': self.hash,'recipient_address': self.recipient_address, 'amount':self.amount})
		recipient_string = json.dumps(info_dict, sort_keys=True)
		return sha256(recipient_string.encode()).hexdigest()

	def compute_hash(self):
		transaction_string = json.dumps(self.to_dict(), sort_keys=True)
		return sha256(transaction_string.encode()).hexdigest()

	def to_dict(self):
		ret = OrderedDict()
		ret['amount'] = self.amount
		ret['sender_address'] = self.sender_address
		ret['recipient_address'] = self.recipient_address
		return ret
	def to_dict_signed(self):
		return OrderedDict({'amount': self.amount, 'sender_address': self.sender_address,'recipient_address': self.recipient_address,'id': self.hash, 'signature': self.signature})

	def sign_transaction(self):
		private_key = RSA.importKey(binascii.unhexlify(self.sender_private_key))
		signer = PKCS1_v1_5.new(private_key)
		print("Signing Transaction")
		#print(self.to_dict())
		message = str(self.to_dict()).encode('utf8')
		h = SHA.new(message)
		signature= binascii.hexlify(signer.sign(h)).decode('ascii')
		return signature
