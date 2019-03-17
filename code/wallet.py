import binascii

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import PKCS1_v1_5

import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
from headers import *

class Wallet:


	def __init__(self, public_key=None, private_key=None):
		if (public_key == None and private_key == None):
			random_gen = Crypto.Random.new().read
			key = RSA.generate(KEY_LEN, random_gen)
			private_key, public_key = key, key.publickey()
			self.public_key = binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
			self.private_key = binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii')
		else:
			self.public_key = public_key
			self.private_key = private_key

		#self.address = PubKey
		#self.transactions = []
		#signer = PKCS1_v1_5.new(PrivKey)
		#digest = SHA.new()
		#digest.update(message)
		#signature = signer.sign(digest)
		#print(signature)
	
	def to_dict(self):
		return OrderedDict({'public_key': self.public_key.exportKey()})
