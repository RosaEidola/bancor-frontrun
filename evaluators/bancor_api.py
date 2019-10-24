import requests
import settings
import time
from models import BancorNetworkToken

def update_currencies(base='ETH'):
    """
    Get currencies from the undocumented API for Bancor

    args:
    base -- base currency in which to calc everything
    """
    url = 'https://api.bancor.network/0.1/currencies/tokens'
    for s in [0, 100]:
        params={'limit':100, 'skip':s, 'fromCurrencyCode':base}
        resp = requests.get(url, params)
        
        for currency in resp.json()['data']['currencies']['page']:
            token, _  = BancorNetworkToken.get_or_create(
                symbol=currency['code'],
                name=currency['name'],
                token_id=currency['_id'])

            # Update the params:
            token.price = currency['price']
            token.liquidity_depth = currency['liquidityDepth']
            token.volume = currency['volume24h']['ETH']
            try:
                time.sleep(0.500)
                txn = get_txn_payload(token, 1e18)
                token.can_trade = True
            except Exception:
                token.can_trade = False
            token.save()

def get_token_amount(token, wei):
    """
    Returns the number of tokens expected to receive
    """
    params = {
        'toCurrencyId' : token.token_id,
        'fromAmount' : wei
    }
    url = 'https://api.bancor.network/0.1/currencies/%s/value'%settings.ETHER_ID
    resp = requests.get(url, params=params)
    
    return int(resp.json()['data'])


def get_txn_payload(token, wei):
    """
    Gets the priviledged TXN payload from the Bancor API

    args:
    amount -- number of ETHER to transact
    from_id -- currency id of the from currency, default Ethereum
    expectedReturn -- 
    """
    url = 'https://api.bancor.network/0.1/transactions/convert' 
    #token_amt = get_token_amount(token, wei)
    params = { 
            'amount': str(wei / 1e18), 
            'fromCurrencyId': settings.ETHER_ID, 
            'hack': "ethereum", 
            'minimumReturn': 1,#(token_amt / (1*10**token.decimals)) * 0.90, 
            'ownerBlockchainId': settings.WALLET, 
            'toCurrencyId': token.token_id, 
    } 
    resp = requests.post(url, data=params) 
    raw_txn = resp.json()['data'][0]['data']['transaction']
    raw_txn['from'] = settings.WEB3.toChecksumAddress(raw_txn['from'])
    raw_txn['to'] = settings.WEB3.toChecksumAddress(raw_txn['to'])

    return raw_txn

