# import from py solcx to compile
from solcx import compile_standard, install_solc
import json
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()

# we need to read contract first
with open("./SimpleStorage.sol", "r") as file:
    simple_storage_file = file.read()

# Compile our solidity
install_solc("0.6.0")
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"SimpleStorage.sol": {"content": simple_storage_file}},
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        },
    },
    solc_version="0.6.0",
)

# Use Json.dump to keep json syntax
with open("compiled_code.json", "w") as file:
    json.dump(compiled_sol, file)

# get bytecode
bytecode = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["evm"][
    "bytecode"
]["object"]

# get abi
abi = json.loads(
    compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["metadata"]
)["output"]["abi"]

# for connecting to ganache (get this from ganache)
# w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
# chain_id = 1337
# my_address = "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1"
# never hard code private keys so using .env var with .gitignore for safety and python dotenv
# private_key = os.getenv("PRIVATE_KEY")

# for connecting to testnet via infura
w3 = Web3(
    Web3.HTTPProvider("https://rinkeby.infura.io/v3/50d7d04f43cd4da2b2fad197194d4138")
)

# rinkeby chain id
chain_id = 4

# address from metamask
my_address = "0xcD2617513997C6AE288b35Ef9E13CD5e2eC1F87d"
# never hard code private keys so using .env var with .gitignore for safety and python dotenv
private_key = os.getenv("PRIVATE_KEY")

# Create the contract in python
SimpleStorage = w3.eth.contract(abi=abi, bytecode=bytecode)
# Get the latest transaction
nonce = w3.eth.getTransactionCount(my_address)

# 1. Build A TRANSACTION
# 2. Sign a transaction
# 3. Send a transaction
transaction = SimpleStorage.constructor().buildTransaction(
    {
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": my_address,
        "nonce": nonce,
    }
)

signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
# Send this signed transaction
print("Deploying contract...")
tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
# this will have code stop and wait for transaction hash to go through
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print("Deployed!")
# Working with contract, you always need
# Contract address
# Contract ABI

simple_storage = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)

# When interacting with blockchain, you can interact with a call or transact
# Call -> Simulate making the call and getting a return value (dont make a state change to blockchain)
# Transact -> Actually make a state change to blockchain

# Initial value of favorite number, no state change so just use call
print(simple_storage.functions.retrieve().call())
# Want to use store function, which makes state change, so we need to build transaction
# Use nonce+1 bc we already used nonce

print("Updating contract...")
store_transaction = simple_storage.functions.store(15).buildTransaction(
    {
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": my_address,
        "nonce": nonce + 1,
    }
)
# Sign it
signed_store_txn = w3.eth.account.sign_transaction(
    store_transaction, private_key=private_key
)
# Send it
send_store_tx = w3.eth.send_raw_transaction(signed_store_txn.rawTransaction)
# Wait for transaction to finish
tx_receipt = w3.eth.wait_for_transaction_receipt(send_store_tx)
print("Updated!")
# call retrieve again and see newly updated value
print(simple_storage.functions.retrieve().call())
