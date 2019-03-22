
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
node = None
param_lock = threading.Lock()

#..........................................................................
	
@app.route('/')
def sessions():
	global node
	print("Let's go!")
	if(not node):	
		print(request.host)
		ip = request.host.split(':',1)[0]
		port = request.host.split(':',1)[1]
		if(ip==BOOTSTRAP_IP and port==BOOTSTRAP_PORT):
			node = Node(ip, port, index=0)
			node.wallet = node.create_wallet()
			node.NBCs.append({'id': '0', 'recipient_address': node.wallet.public_key, 'amount':NUM_OF_NODES * 100})
			node.ring.append({'id': node.index, 'ip': ip,'port': port, 'public_key': node.wallet.public_key})
			print("Bootstrap node successfully added!")
			print("My id: " + str(node.index))
		else:	
			node = Node(ip, port)
			node.wallet = node.create_wallet()
			while True:
				response = requests.get("http://" + BOOTSTRAP_IP + ":" + BOOTSTRAP_PORT + "/init_node?ip="+ip+"&port="+ port + "&public_key="+node.wallet.public_key)
				if response.status_code != 503:
					break
			if(response.status_code == 200):
				nid=response.json()['id']
				node.index=int(nid)
				blockchain_json= response.json()['blockchain']
				node.chain = Blockchain(node.index, blockchain_json['unconfirmed_transactions'], blockchain_json['chain'])
				if(node.valid_chain()):
					print("I got a valid blockchain!")
				else:
					print("My first blockchain is false :( ")
				while True:
					response = requests.post("http://" + BOOTSTRAP_IP + ":" + BOOTSTRAP_PORT + "/first_transaction?id="+ str(nid))
					if response.status_code != 503:
						break
				if(response.status_code == 200):
					output = response.json()['output']
					node.NBCs.append(output)
					print("Median node added successfully!")
		if(node.index == NUM_OF_NODES-1):
			print("Oops! It was the last one!")
			while True:
				response = requests.post("http://" + BOOTSTRAP_IP + ":" + BOOTSTRAP_PORT + "/nodes_ready")
				if response.status_code != 503:
					break
	return render_template('homepage.html'), 200

@app.route('/create')
def new_transaction_session():
	return render_template('session.html')

@app.route('/init_node', methods=['GET'])
def init_node():
	global node 
	#if node.busy == True:
	#	return jsonify({'status': 'Try again'}), 503
	#node.busy=True
	nid= node.current_id_count
	node.current_id_count+=1 #for next node
	
	PubKey = request.args.get('public_key')
	ip=request.args.get('ip')
	port=request.args.get('port')
	#Adding new node info in bootstrap's ring
	node.ring.append({'id': nid, 'ip': ip, 'port': port, 'public_key': PubKey})
	
	response = {'blockchain': node.chain.to_dict(),'id': nid}
	#node.busy=False
	return jsonify(response),200 #Sending Key and id
	
@app.route('/first_transaction', methods=['POST'])
def first_transaction():
	global node
	#if node.busy == True:
	#	return jsonify({'status': 'Try again'}), 503
	#node.busy=True
	nid = int(request.args.get('id'))
	for n in node.ring:
		if(n['id'] == nid):
			recipient_node = n
	recipient_public_key = recipient_node['public_key']
	new_transaction= node.create_transaction(node.wallet.public_key, recipient_public_key, 100, node.NBCs)
	transaction = new_transaction['transaction']
	signature = new_transaction['signature']
	outputs = new_transaction['outputs']
	if(node.broadcast_transaction(transaction, signature, outputs)==-1):
		return jsonify({'status': 'Error'}), 500
	node.add_transaction_to_block(new_transaction)
	if(len(node.chain.unconfirmed_transactions)==BLOCK_SIZE):
		#node.busy=False
		if(node.broadcast_mine_block(node.chain.unconfirmed_transactions)==-1):
			return jsonify({'status': 'Error'}), 500
	node.NBCs = [outputs['sender']]
	response = {'output': outputs['recipient']}
	#node.busy=False
	return jsonify(response), 200

@app.route('/create/new_transaction', methods=['POST'])
def new_transaction():
	global node
	if node.busy == True:
		return jsonify({'status': 'Try again'}), 503
	node.busy=True
	print("Sending transaction!")
	nid = int(request.args.get('id'))  
	#nid = int(request.form['id'])
	print("Receipient id is" + str(nid))
	amount = int(request.args.get('amount'))
	#amount = int(request.form['amount'])
	print("amount is" + str(amount))
	for n in node.ring:
		if(n['id'] == nid):
			recipient_node = n
		#print("recipient node is" + str(recipient_node))
	recipient_public_key = recipient_node['public_key']
	new_transaction= node.create_transaction(node.wallet.public_key, recipient_public_key, amount, node.NBCs)
	transaction = new_transaction['transaction']
	print("transaction created!")
	signature = new_transaction['signature']
	outputs = new_transaction['outputs']
	print("About to broadcast")
	ret = node.broadcast_transaction(transaction, signature, outputs)
	if ret ==-1:
		print("Broadcast Error")
		return jsonify({'status': 'Error'}), 500
	if ret != -2:
		node.add_transaction_to_block(new_transaction)
		print("Last block transactions count: ")
		print(len(node.chain.unconfirmed_transactions))
		if((len(node.chain.unconfirmed_transactions)>=BLOCK_SIZE) and (node.index != 0)):
			#while True:
			response = requests.post("http://" + BOOTSTRAP_IP + ":" + BOOTSTRAP_PORT + "/we_should_mine")
				#if response.status_code != 503:
					#break
			#node.busy=True
			#if(node.broadcast_mine_block(node.chain.unconfirmed_transactions)==-1):
			#	return jsonify({'status': 'Error'}), 500
			#node.busy=True
		node.NBCs = [outputs['sender']]
		print('Transaction Verified and Ready to be Sent')
		response = outputs['recipient']
		while True:
			r = requests.post("http://" + node.ring[nid]['ip'] + ":" + node.ring[nid]['port'] + "/receive_transaction", json=outputs['recipient'])
			if r.status_code != 503:
				break
			if(r.status_code != 200):
				return jsonify({'status': 'Error'}), 500
	node.busy=False
	return jsonify(response), 200

@app.route('/we_should_mine', methods=["POST"])
def lets_mine():
	global node
	if node.busy == True:
		return jsonify({'status': 'Try again'}), 503
	if(len(node.chain.unconfirmed_transactions)>=BLOCK_SIZE):
		#node.busy=True
		ready_transactions=node.chain.unconfirmed_transactions[:BLOCK_SIZE]
		#for transaction in ready_transactions:
		#	ret = node.broadcast_validate(transaction)
		#	if ret ==-1:
		#		print("Broadcast Error")
		#		return jsonify({'status': 'Error'}), 500
		if(node.broadcast_mine_block(ready_transactions)==-1):
			return jsonify({'status': 'Error'}), 500	
	node.busy=False
	return jsonify({'status': 'OK'}), 200

@app.route('/mine', methods=['POST'])
def mine():
	global node
	#if node.busy == True:
	#	return jsonify({'status': 'Try again'}), 503
	node.busy=True
	print("About to Mine :-)")
	new_block= node.create_new_block(request.json)
	mined_block = node.mine_block(new_block)
	if(mined_block == 0):
		return jsonify({'status': 'OK'}), 200
	if(node.broadcast_block(mined_block)!=0):
		return jsonify()
	node.chain.chain.append(mined_block)
	for i in range(BLOCK_SIZE):
		node.chain.unconfirmed_transactions.pop(0)
	#node.chain.unconfirmed_transactions = []
		#	return 0
	node.busy=False
	return jsonify({'status': 'OK'}), 200

@app.route('/receive_transaction', methods=['POST'])
def receive_transaction():
	global node
	#if node.busy == True:
	#	return jsonify({'status': 'Try again'}), 503
	#node.busy=True
	output = request.json
	node.NBCs.append(output)
	#node.busy=False
	return jsonify({'status': 'OK'}), 200

@app.route('/get_mined_block', methods=['POST'])
def get_mined_block():
	global node
	#if node.busy == True:
	#	return jsonify({'status': 'Try again'}), 503
	node.busy=True
	mined_block = request.json['block']
	if(len(node.chain.chain) != mined_block['index']):
		print('Got it from someone else')
		return jsonify({'status': 'OK'}), 200
	node.chain.chain.append(mined_block)
	for i in range(BLOCK_SIZE):
		node.chain.unconfirmed_transactions.pop(0)
	print("My chain now: ")
	#print(node.chain.chain)
	print("Transactions left unconfirmed")
	print(len(node.chain.unconfirmed_transactions))
	if(node.valid_chain()):
		print("My chain is valid")
	else:
		print("Something wrong with my chain :-( ")	
	node.busy=False
	return jsonify({'status':'OK'}), 200

@app.route('/nodes_ready', methods=['POST'])
def nodes_ready():
	global node
	#if node.busy == True:
	#	return jsonify({'status': 'Try again'}), 503
	node.busy=True
	for current_node in node.ring:
		if(current_node['ip']!=BOOTSTRAP_IP or current_node['port']!=BOOTSTRAP_PORT):
			while True:
				response = requests.post('http://' + current_node['ip'] + ':' + current_node['port'] + '/get_ring', json=node.ring)
				if response.status_code != 503:
					break
			if(response.status_code != 200):
				return jsonify({'status':'Error'}), 400
	node.busy=False
	return jsonify({'status': 'OK'}), 200

@app.route('/get_ring', methods=['POST'])
def get_my_ring():
	global node
	#if node.busy == True:
	#	return jsonify({'status': 'Try again'}), 503
	#node.busy=True
	ring=request.json
	node.ring=ring
	#node.busy=False
	return jsonify({'status': 'OK'}), 200

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
	global node
	if(node.add_transaction_to_block(request.json)==0):
		return jsonify({'status': 'OK'}), 200
	else:
		return jsonify({'status': 'Error! Invalid Transaction'}), 400
	
@app.route('/validate_transaction', methods=['POST'])
def validate_trans():
	global node
	#if node.busy == True:
		#return jsonify({'status': 'Try again'}), 503
	#node.busy=True
	if(node.validate_transaction(request.json)==0):
		#node.busy=False
		return jsonify({'status': 'OK'}), 200
	else:
		#node.busy=False
		return jsonify({'status': 'Error! Invalid Transaction'}), 400

@app.route('/run_5')
def run_5():
	global node
	#node.busy =False
	path = "../transactions/5nodes/transactions" + str(node.index) + ".txt"
	file = open(path, "r")
	#line = file.readline()
	for line in file:
		print('Next Line')
		print(line)
		if line == "\n":
			break 
		recipient, amount_first = line.split(" ",1)
		amount = amount_first.split("\n",1)[0]
		print(amount)
		recipient_id = recipient[2]
		while True:
			response = requests.post('http://' + node.ip + ':' + node.port + '/create/new_transaction?id=' + recipient_id + '&amount=' + str(int(amount)))
			if response.status_code != 503:
				break
		if(response.status_code != 200):
			print('Some error!')
			return jsonify({'status': 'error'}), 500 
	return jsonify({'first_line': line}), 200

@app.route('/valid_chain')
def valid_chain():
	global node
	if(node.valid_chain()):
		return jsonify({'blockchain': node.chain.chain, 'unconfirmed_transactions': node.chain.unconfirmed_transactions})
	else:
		return jsonify({'status': 'Error! Invalid blockchain'}), 500

@app.route('/get_chain', methods=['POST'])
def get_chain():
	global node	
	#if node.busy == True:
	#	return jsonify({'status': 'Try again'}), 503
	#node.busy=True
	length = len(node.chain.chain)
	chain = node.chain.to_dict()
	response = {'length': length, 'chain': chain}
	#node.busy=False
	return jsonify(response), 200
	
@app.route('/balance')
def balance():
	global node
	#if node.busy == True:
	#	return jsonify({'status': 'Try again'}), 503
	#node.busy=True
	cash = node.balance()
	#node.busy=False
	return render_template('balance.html', cash=cash)

@app.route('/view')
def view():
	global node
	#if node.busy == True:
	#	return jsonify({'status': 'Try again'}), 503
	#node.busy=True
	last_block = node.chain.chain[-1]
	response = {'transactions': last_block['transactions']['transaction']}
	#node.busy=False
	return render_template('view.html',last_transactions=jsonify(response))

@app.route('/help')
def help():
	return render_template('help.html')

if __name__ == '__main__':   #Skeletos
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    #parser.add_argument('ip')
    args = parser.parse_args()
    port = args.port
    #ip = args.ip
    #app.run()
    socketio.run(app, host='127.0.0.1', port=port)
