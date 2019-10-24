"""
Utility functions 


DLF 2019
"""
import settings
from web3 import Web3
from ethereum_input_decoder import ContractAbi
import requests


def contract_from_address(address, as_web3=True):
    """
    Create a contract from an address using Etherscan API
    """
    if not address:
        address = settings.BANCOR_MONITOR_ADDRESSES[0]
    params={
        'module' : 'contract',
        'action' : 'getabi',
        'address' : settings.WEB3.toChecksumAddress(address), 
        'apikey' : settings.ETHERSCAN_API_KEY
        }
    resp = requests.get('http://api.etherscan.io/api', params)
    abi = resp.json()['result']
    contract = settings.WEB3.eth.contract(abi=abi, address=address)
    
    if not as_web3:
        contract = ContractAbi(contract.abi)

    return contract


def generic_erc20_contract(address):
    """
    Return a generic contract ABI for an ERC 20 token, without having to 
    fetch the ABI data from external sources (performance...)
    """
    abi = [
        {'constant': True,
         'inputs': [],
         'name': 'symbol',
         'outputs': [{'name': '', 'type': 'string'}],
         'payable': False,
        'type': 'function'},
        {'constant': True,
         'inputs': [],
         'name': 'decimals',
         'outputs': [{'name': '', 'type': 'uint8'}],
         'payable': False,
         'type': 'function'},
    ]
    return settings.WEB3.eth.contract(abi=abi, address=address)

