import requests
import settings
import lxml.html as lh


class EtherScan(object):
    """
    Class for making calls to EtherScan API
    """
    host = 'https://api.etherscan.io/api'

    def __init__(self, api_key=settings.ETHERSCAN_API_KEY):
        """
        Initialize
        """

        self.api_key = api_key



    def get_txn(self, txn_hash):
        """
        Returns information about a txn hash
        """
        params = {
            'txhash' : txn_hash,
            'action' : 'eth_getTransactionByHash',
            'apikey' : self.api_key,
            'module' : 'proxy'
        }
        resp = requests.get(self.host, params=params).json()
        return resp['result']


    def scrape_pending_txns(self, address=settings.BANCOR_MONITOR_ADDRESSES[0]):
        """
        Get the pending transaction on a given address
        """
        resp = requests.get('https://etherscan.io/address/%s'%address)
        doc = lh.fromstring(resp.content.decode())

        # Find pending txns via xpath:
        pending_txns = doc.xpath(".//*[contains(text(),'(Pending)')]/../../..")
        pending_txns = [x[0][0][0].text for x in pending_txns]
        
        return pending_txns