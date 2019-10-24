"""
Constantly monitor the node's transaction pool for 
valid transactions that meet our criteria 

"""
from web3 import Web3
from models import TransactionLog
from evaluators.BancorEvaluator import BancorEvaluator
from etherscan import EtherScan
import settings
import time

class TransactionScanner(object):
    """
    Scan Etherscan for relevant txns
    """

    client = EtherScan()
    evaluator = BancorEvaluator()
    have_seen = set()

    def scan(self):
        """
        Start the scanner
        """

        while 1:
            time.sleep(2)

            tx_hashes = self.client.scrape_pending_txns()

            for tx_hash in tx_hashes:

                # Avoid duplication:
                if tx_hash in self.have_seen:
                    continue
                self.have_seen.add(tx_hash)

                # Get the txn information:
                txn = self.client.get_txn(tx_hash)
                token, log = self.evaluator.parse_txn(txn, is_hash=False)
                print(token, log)
                self.evaluator.evaluate(txn)
                #token, log = self.evaluator.parse_txn(txn, is_hash=False)
                #print(token, log)












'''
class TransactionPoolScanner(object):
    """
    Class for handling pool scanning for a given node
    """

    def __init__(self, host='http://127.0.0.1', port=8545):
        """
        Initialize the scanner for a given node
        
        Args:
        host -- RPC host string, defaults to 'http://127.0.0.1'
        port -- port of RPC, default 8545
        """
        self.provider = Web3.HTTPProvider(host + ':' + str(port))
        self.web3 = Web3(self.provider)
        self.info = self.web3.admin.nodeInfo

        print("Pool Scanner for {0}".format(self.info['ip']))

    def scan_txpool(self):
        """
        Run a scan on the txpool. No args or outputs
        """
        while 1:
            txpool = self.web3.txpool.content.pending 

            passes_criteria = 0
            for tx_hash in txpool:

                # Why do I need to do this?
                txn = dict(txpool[tx_hash])
                txn = dict(txn[list(txn.keys())[0]])
                txn['from'] = tx_hash

                txn_log = TransactionLog.from_raw_txn(txn)
                passes, evaluator = self.txn_passes_criteria(txn_log)
                if passes:
                    print('Bancor Txn Detected...')
                    # TO DO: CALL TRADE EVALUATOR!
                    # evaluator.evaluate(txn_log)
                    #txn_log.save()
                    #passes_criteria += 1

            if passes_criteria:
                print('{0}/{1} Txns passed criteria'.format(passes_criteria, len(txpool)))


    def txn_to_log(self, txn):
        """
        Returns a normalized TransactionLog object 

        Args:
        txn -- a txn dictionary to log

        Returns:
        txn_log -- a normalized TransactionLog object 
        """
        return TransactionLog(
            block_hash=txn['blockHash'],
            from_addr=txn['from'],
            gas=self.web3.toInt(hexstr=txn['gas']),
            gas_price=self.web3.toInt(hexstr=txn['gasPrice']),
            txn_hash=txn['hash'],
            input_data=txn['input'],
            nonce=web3.toInt(hexstr=txn['nonce']),
            to_addr=txn['to'],
            txn_index=txn['value'],
            value=web3.toInt(hexstr=txn['value']),
            detected_by=self.info['ip']
        )

    def txn_passes_criteria(self, txn_log):
        """
        Does the given txn pass our criteria for being relevant?
        
        Args:
        txn_log -- a TransactionLog object to evaluate
        
        Returns:
        passes_criteria -- boolean, does the txn pass criteria
        evaluator -- relevant evaluation object given the txn
        """
        if txn_log.to_addr in settings.BANCOR_MONITOR_ADDRESSES:
            return True, object

        # TO DO: Add other evaluators for other markets to front run?
        return False, None



'''