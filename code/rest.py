
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
	if(not node):	
		print(request.host)
		ip = request.host.split(':',1)[0]
		port = request.host.split(':',1)[1]
		if(ip==BOOTSTRAP_IP):
			node = Node(ip, port, index=0)
			node.wallet = node.create_wallet()
			node.NBCs.append({'id': '0', 'recipient_address': node.wallet.public_key, 'amount':NUM_OF_NODES * 100})
			node.ring.append({'id': node.index, 'ip': ip,'port': port, 'public_key': node.wallet.public_key})
			print("Bootstrap node successfully added!")
			print("My id: " + str(node.index))
		else:	
			node = Node(ip, port)
			node.wallet = node.create_wallet()
			response = requests.get("http://" + ip + ":" + port + "/init_node?ip="+ip+"&port="+ port + "&public_key="+node.wallet.public_key)
			if(response.status_code == 200):
				nid=response.json()['id']
				node.index=int(nid)
				blockchain_json= response.json()['blockchain']
				node.chain = Blockchain(node.index, blockchain_json['unconfirmed_transactions'], blockchain_json['chain'])
				response = requests.post("http://" + ip + ":" + port + "/first_transaction?id="+ str(nid))
				if(response.status_code == 200):
					output = response.json()['output']
					node.NBCs.append(output)
					print("Median node added successfully!")
		if(node.index == NUM_OF_NODES-1):
			print("Oops! It was the last one!")
			response = requests.post("http://" + ip + ":" + port + "/nodes_ready")
			
			#for node in other_nodes:
				#node.ring=bootstrap_node.ring
		#return "Node Added! Your port is: " + port , 201
	else: 
		#return "Homepage!", 200
	return render_template('homepage.html'), 200

@app.route('/create')
def new_transaction_session():
	return render_template('session.html')

@app.route('/init_node', methods=['GET'])
def init_node():
	global node #, blockchain
	#Initializing its id	
	nid= node.current_id_count
	node.current_id_count+=1 #for next node
	
	PubKey = request.args.get('public_key')
	ip=request.args.get('ip')
	port=request.args.get('port')
	#Adding new node info in bootstrap's ring
	node.ring.append({'id': nid, 'ip': ip, 'port': port, 'public_key': PubKey})
	
	response = {'blockchain': node.chain.to_dict(),'id': nid}
	return jsonify(response),200 #Sending Key and id
	
@app.route('/first_transaction', methods=['POST'])
def first_transaction():
	global node
	nid = int(request.args.get('id'))
	recipient_public_key = node.ring[nid]['public_key']
	new_transaction= node.create_transaction(node.wallet.public_key, recipient_public_key, 100, node.NBCs)
	transaction = new_transaction['transaction']
	signature = new_transaction['signature']
	outputs = new_transaction['outputs']
	if(node.broadcast_transaction(transaction, signature, outputs)==-1):
		return jsonify({'status': 'Error'}), 500
	node.NBCs = [outputs['sender']]
	response = {'output': outputs['recipient']}
	#print(response)
	return jsonify(response), 200

@app.route('/create/new_transaction', methods=['POST'])
def new_transaction():
	global node
	nid = int(request.form['id'])
	amount = int(request.form['amount'])
	recipient_public_key = node.ring[nid]['public_key']
	new_transaction= node.create_transaction(node.wallet.public_key, recipient_public_key, amount, node.NBCs)
	transaction = new_transaction['transaction']
	signature = new_transaction['signature']
	outputs = new_transaction['outputs']
	if(node.broadcast_transaction(transaction, signature, outputs)==-1):
		return jsonify({'status': 'Error'}), 500
	node.NBCs = [outputs['sender']]
	print("My precious output: ")
	print(outputs['sender'])
	print("Sending this output: ")
	print(outputs['recipient'])
	response = outputs['recipient']
	r = requests.post("http://" + node.ring[nid]['ip'] + ":" + node.ring[nid][port] + "/receive_transaction", json=outputs['recipient'])
	if(r.status_code != 200):
		return jsonify({'status': 'Error'}), 500
	return jsonify(response), 200

@app.route('/receive_transaction', methods=['POST'])
def receive_transaction():
	global node
	output = request.json
	node.NBCs.append(output)
	return jsonify({'status': 'OK'}), 200

@app.route('/get_mined_block', methods=['POST'])
def get_mined_block():
	global node
	mined_block = request.json['block']
	transaction = request.json['transaction']
	if(len(node.chain.chain) != mined_block['index']):
		print('Got it from someone else')
		return jsonify({'status': 'OK'}), 200
	node.chain.chain.append(mined_block)
	node.chain.unconfirmed_transactions = [transaction]
	print("My chain now: ")
	print(node.chain.chain)
	print("New transaction: ")
	print(node.chain.unconfirmed_transactions)	
	return jsonify({'status':'OK'}), 200

@app.route('/nodes_ready', methods=['POST'])
def nodes_ready():
	global node
	for current_node in node.ring:
		if(current_node['ip']!=BOOTSTRAP_IP):
			response = requests.post('http://' + current_node['ip'] + ':' + current_node['port'] + '/get_ring', json=node.ring)
			if(response.status_code != 200):
				return jsonify({'status':'Error'}), 400
	return jsonify({'status': 'OK'}), 200

@app.route('/get_ring', methods=['POST'])
def get_my_ring():
	global node
	ring=request.json
	node.ring=ring
	return jsonify({'status': 'OK'}), 200
		
@app.route('/validate_transaction', methods=['POST'])
def validate_trans():
	global node
	if(node.validate_transaction(request.json)==0):
		return jsonify({'status': 'OK'}), 200
	else:
		return jsonify({'status': 'Error! Invalid Transaction'}), 400

@app.route('/run_5')
def run_5():
	global node
	path = "../transactions/5nodes/transactions" + str(node.index) + ".txt"
	file = open(path, "r")
	line = file.readline()
	return jsonify({'first_line': line}), 200

@app.route('/valid_chain')
def valid_chain():
	global node
	if(node.valid_chain()):
		return jsonify({'blockchain': node.chain.chain, 'unconfirmed_transactions': node.chain.unconfirmed_transactions})
	else:
		return jsonify({'status': 'Error! Invalid blockchain'}), 500

@app.route('/balance')
def balance():
	global node
	cash = node.balance()
	return render_template('balance.html', cash=cash)

@app.route('/view')
def view():
	global node
	last_block = node.chain.chain[-1]
	response = {'transactions': last_block['transactions']['transaction']}
	return render_template('view.html',last_transactions=jsonify(response))

@app.route('/help')
def help():
	return render_template('help.html')

if __name__ == '__main__':   #Skeletos
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('ip', required=True)
    args = parser.parse_args()
    port = args.port
    ip = args.ip
    #app.run()
    socketio.run(app, host=ip, port=port)
