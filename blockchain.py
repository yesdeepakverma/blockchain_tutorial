"""
block = {
    index: 1,
    timestamp: 12312312423234234.123123, # unix timestamp
    transactions: [
        {
            sender: '123121jg3kjh1g23hjf1hj23k1hj23g',
            recipient: '23hj2g3kh4jg2h34gkh2jg4kjh234,
            amount: 5
        }
    ],
    proof: 12365126351732657,
    previous_hash: "12ekjhkqwhe7i7834786yn327ny87qdyn387dny78hfn87qhf874hf734h8hq34fo7hqn34ifhbq34ifbi43b"
}


Hint: eveny block contains the hash of the previous block

"""
import hashlib
import json
from time import time
from textwrap import dedent
from uuid import uuid4

import requests
from flask import Flask, jsonify, request


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        self.new_block(previous_hash='1', proof=100)
    
    def register_node(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError("Invalid URL")
        
    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print('{}'.format(last_block))
            print('{}'.format(block))

            if block['previous_hash'] != self.hash(last_block):
                return False

            if not self.valid_proof(last_block['proof'], block['proof'], last_block['previous_hash']):
                return False
            last_block = block
            current_index += 1
        return True

    def resolve_conflict(self):
        """
        this is our consensus algorithm, it resolves conflicts by replacing our chain with the longest
        one in the network.

        :return: True if our chain was replaced, False of not
        """
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get('http://{}/chain'.format(node))
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length  and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        return False

    
    def proof_of_work(self, last_proof):
        """
        Simeple proof of Work Algorithm
        - find anumber p' sych that hash(pp') contains leading 4 zeros, where p is the prevuious p'
        - p is the previous proof, and p' is the new proof

        :param last_proof: int
        :return: int
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the proofL Does hash(last_proof, proof) contains 4 leading zeros

        :param last_proof: <int> Previous Proof
        :prarm proof: int Current proof
        :return <bool> True if correct, False if not
        """

        guess = '{}{}'.format(last_proof, proof).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def new_block(self, proof, previous_hash=None):
        """created a new block and adds it to the chain
        
        Create a new Block in the Blockchain

        :param proof: <int> the proof given by the proof of work alo
        :param previous_hash: Optional <str> hashof the previuos Block
        :return: <dict> New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions':self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []
        self.chain.append(block)
        return block
    
    def new_transaction(self, sender, recipient, amount):
        """
        Created a new transaction to go into the next mined Block

        :param sender: address of the sender
        :param recipient:  address of the recupient
        :param amount: Amount

        :return: <int> The index of the Block that will hold this transctions
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })
        return self.last_block['index']+1

    
    @staticmethod
    def hash(block):
        """
        creates a SHA-256 hash of a Block
        :param block: <dict> Block
        :return: <str>
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # returns the last block in the chain
        return self.chain[-1]


app = Flask(__name__)
node_identifier = str(uuid4()).replace("-", '')
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']

    proof = blockchain.proof_of_work(last_proof)

    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1
    )
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    balues = request.get_json()

    required = ['sender', 'recipient', 'amount']

    if not all(k in values for k in required):
        return 'Missing balues', 400

    index = blockchain.new_transaction(values['sender'], values['recipient'], value['amount'])
    response = {'message': 'Transaction will be added to Block {}'.format(index)}
    return jsonify(response), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
