import json
import os
import sys

from dotenv import load_dotenv
from loguru import logger
from time import sleep
from web3 import Web3

from web3.middleware import geth_poa_middleware


def get_abi():
    # Getting the ABI from the contract
    try:
        with open('abi.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


# Loading environment variables
load_dotenv()

BSC = os.getenv('BSC')
ADDRESS = os.getenv('ADDRESS')
TOKEN_ADDRESS = os.getenv('TOKEN_ADDRESS')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
ABI = get_abi()

# Connecting to BSC end point
web3 = Web3(Web3.HTTPProvider(BSC))
# Adding middleware
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Checking if a succesful connection was made
assert web3.is_connected(), "Connection failed"
logger.info("Connection successful")

# Connecting to token address
token_addres = web3.to_checksum_address(TOKEN_ADDRESS)
contract = web3.eth.contract(address=token_addres, abi=ABI)
logger.info(f"Conneced to {token_addres}")

while True:
    try:
        # Creating the function call
        function_call = contract.functions.hatchEggs

        # Estimating the gas for the transaction
        gas_estimate = function_call(ADDRESS).estimate_gas({'from': ADDRESS})
        logger.info(f"Gas estimates: {gas_estimate}")

        # Get the current gas price from the network
        gas_price = web3.eth.gas_price
        logger.info(
            f"Total gas price: {web3.from_wei(gas_price, 'ether') * gas_estimate}")

        # Get the nonce value for the sender address
        nonce = web3.eth.get_transaction_count(ADDRESS)
        logger.info(f"Nonce: {nonce}")

        # Build the transaction
        hatch_transaction = function_call(ADDRESS).build_transaction({
            'from': ADDRESS,
            'gas': gas_estimate,
            'gasPrice': gas_price,
            'nonce': nonce
        })
        logger.info(f"Transaction: {hatch_transaction}")

        # Sign and send the transaction
        signed_txn = web3.eth.account.sign_transaction(
            hatch_transaction, PRIVATE_KEY)
        web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        logger.info("Succesfully send transaction")

        logger.info("Waiting 30 minutes before hatching eggs again")
        sleep(1800)
    except KeyboardInterrupt:
        logger.info("User initiated graceful shutdown")
        sys.exit(0)
