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

KEY_LEN = 2048

class wallet:


	def __init__(self):  # Diko mou gia dimiourgia kleidiwn kai upografis (vlepe Crypto vivliothikes)
		##set
		key = RSA.generate(KEY_LEN)

		message = b'Generic Message'

		PrivKey, PubKey = key, key.publickey()

		signer = PKCS1_v1_5.new(PrivKey)

		digest = SHA.new()

		digest.update(message)

		signature = signer.sign(digest)

		print(signature)

		self.public_key = PubKey
		self.private_key = PrivKey
		self.address = PubKey
		#self.transactions

	#def balance():

print("Let's go!\n")
wallet()
print("END!\n")