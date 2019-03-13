
from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO, send
from flask_cors import CORS

from headers import *

from block import Block, Blockchain
from node import Node
from wallet import Wallet
from transaction import Transaction
from wallet import Wallet
import threading
### JUST A BASIC EXAMPLE OF A REST API WITH FLASK

import requests

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import PKCS1_v1_5

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
CORS(app)
#blockchain = None
#wallet = None
node = None
#nid = -1
#port = ''
#other_nodes = []
param_lock = threading.Lock()

#.......................................................................................

@socketio.on('connect')
def connect():
	global node #, nid, port, blockchain, wallet
	print(request.host)
	port = request.host.split(':',1)[1]
	print(port)
	if(port==BOOTSTRAP_PORT):
		node = Node(HOST, port, index=0)
		node.wallet = node.create_wallet()
		node.ring.append({'id': node.index, 'port': port, 'public_key': node.wallet.public_key})
		print("Bootstrap node successfully added!")
		print("My id: " + str(node.index))
	else:	
		node = Node(HOST, port)
		node.wallet = node.create_wallet()
		response = requests.get("http://" + HOST + ":" + BOOTSTRAP_PORT + "/init_node?port="+port+"&public_key="+node.wallet.public_key)
		if(response.status_code == 200):
			nid=response.json()['id']
			node.index=int(nid)
			response = requests.post("http://" + HOST + ":" + BOOTSTRAP_PORT + "/first_transaction?id="+ str(nid))
			if(response.status_code == 200):
				blockchain_json= response.json()['blockchain']
				node.chain = Blockchain(node.index, blockchain_json['unconfirmed_transactions'], blockchain_json['chain'])
				print("CHAIN IS: ")
				print(node.chain.to_dict())
				print("Median node added successfully!")
	if(node.index == NUM_OF_NODES-1):
		print("Oops! It was the last one!")
		response = requests.post("http://" + HOST + ":" + BOOTSTRAP_PORT + "/nodes_ready")
		
		#for node in other_nodes:
			#node.ring=bootstrap_node.ring
	return "Node Added! Your port is: " + port , 201

@app.route('/')
def sessions():
	return render_template('index.html')

@app.route('/init_node', methods=['GET'])
def init_node():
	global node #, blockchain
	#Initializing its id	
	nid= node.current_id_count
	node.current_id_count+=1 #for next node
	
	PubKey = request.args.get('public_key')
	port=request.args.get('port')
	#Adding new node info in bootstrap's ring
	node.ring.append({'id': nid, 'port': port, 'public_key': PubKey})
	
	response = {'id': nid}
	return jsonify(response),200 #Sending Key and id
	
@app.route('/first_transaction', methods=['POST'])
def first_transaction():
	global node
	nid = int(request.args.get('id'))
	recipient_public_key = node.ring[nid]['public_key']
	new_transaction= node.create_transaction(node.wallet.public_key, recipient_public_key, 100)
	transaction = new_transaction['transaction']
	signature = new_transaction['signature']
	if(node.broadcast_transaction(transaction, signature)==-1):
		return jsonify({'status': 'Error'}), 500
	node.add_transaction_to_block(new_transaction)
	response = {'blockchain': node.chain.to_dict()}
	print(response)
	return jsonify(response), 200

@app.route('/nodes_ready', methods=['POST'])
def nodes_ready():
	global node
	print("My ring: ")
	print(node.ring)
	for current_node in node.ring:
		if(current_node['port']!=BOOTSTRAP_PORT):
			response = requests.post('http://' + HOST + ':' + current_node['port'] + '/get_ring', json=node.ring)
			if(response.status_code != 200):
				return jsonify({'status':'Error'}), 400
	return jsonify({'status': 'OK'}), 200

@app.route('/get_ring', methods=['POST'])
def get_my_ring():
	global node
	ring=request.json
	print("I got this ring: ")
	print(ring)
	node.ring=ring
	return jsonify({'status': 'OK'}), 200
		
@app.route('/validate_transaction', methods=['POST'])
def validate_trans():
	global node
	#transaction=request.json
	if(node.validate_transaction(request.json)==0):
		return jsonify({'status': 'OK'}), 200
	else:
		return jsonify({'status': 'Error! Invalid Transaction'}), 400
	
# get all transactions in the blockchain

@app.route('/transactions/get', methods=['GET'])  # Apo ton skeleto
def get_transactions():
    transactions = blockchain.unconfirmed_transactions

    response = {'transactions': blockchain.unconfirmed_transactions}
    return jsonify(response), 200

@app.route('/transactions', methods=['POST'])
def new_transactions():
	tx_data = request.get_json()
	required_fields = ["sender_address", "recipient_address", "amount"]
	for field in required_fields:
		if not tx_data.get(field):
			return "Invalid transaction data", 400
	ret = create_transaction(tx_data['sender_address'], tx_data['recipient_address'], tx_data['amount'])
	if(ret == 0):
		return "Transaction Added!", 201
	else:
		return "Post Error!", 400
	

#@app.route('/generate/transaction', methods=['POST']) #Copy-paste
#def generate_transaction():

  #sender_address = request.form['sender_address']
  #sender_private_key = request.form['sender_private_key']
  #recipient_address = request.form['recipient_address']
  #value = request.form['amount']

  #transaction = Transaction(sender_address, sender_private_key, recipient_address, value)

  #response = {'transaction': transaction.to_dict(), 'signature': transaction.sign_transaction()}

  #return jsonify(response), 200

@app.route('/wallet/new', methods=['GET']) #Copy-paste
def new_wallet():
  random_gen = Crypto.Random.new().read
  private_key = RSA.generate(1024, random_gen)
  public_key = private_key.publickey()
  response = {
    'private_key': binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
    'public_key': binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
  }

  return jsonify(response), 200

# run it once fore every node

if __name__ == '__main__':   #Skeletos
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    
    #app.run()
    socketio.run(app, host='127.0.0.1', port=port)
