"""
Caching mechanism for Bancor requests allowing for faster online
processing of frontrunning

Need to:
Create a cache for every token in the network, for a couple different
amounts.  Need up drop entries when _maxBlock >= current_block, and 
when max_gas_price changes.
"""
from settings import contract_from_address, WEB3, BANCOR_CONTRACT
from models import BancorNetworkToken, TransactionLog
from evaluators.bancor_api import get_txn_payload
from multiprocessing import Queue 
from threading import Thread
import time


class BancorCache(object):
    """
    Interface to handling caches
    """

    gas_limit_addr = '0x607a5C47978e2Eb6d59C6C6f51bc0bF411f4b85a'
    gas_limit_contract = None
    current_gas_limit = 0
    amounts = [1,]
    cache = {}
    update_queue = []
    num_threads = 1


    def __init__(self, start=False):
        """
        Initialze some params
        """
        self.gas_limit_contract = contract_from_address(self.gas_limit_addr)
        self.tokens = list(BancorNetworkToken.select().where((BancorNetworkToken.volume>30) & (BancorNetworkToken.can_trade)))
        self.update_current_gas_limit()

        # Start the updater threads
        #for t in range(self.num_threads):
        #    thread = Thread(target=self.txn_worker)
        #    thread.start()

        #if start:
        #    self.start_update_worker()

    def start_update_worker(self, wait_on_complete=False):
        """
        Starts the worker
        """

        if wait_on_complete:
            print('Pre-caching all objects before daemon')
            self.update_current_gas_limit()
            self.update_cache()
            while 1:
                if len(self.cache.keys()) >= len(self.tokens):
                    break
                time.sleep(1)

        print('Starting background cache update daemon')
        def update_worker(self):
            while 1:
                self.update_current_gas_limit()
                self.update_cache()
                time.sleep(1.5)
        thread = Thread(target=update_worker, args=(self, ))
        thread.start()

    def txn_worker(self):
        """
        A background thread worker for updating asyncronously
        """
        while 1:
            time.sleep(.300)

            try:
                if not self.update_queue:
                    continue
                (symbol, amount) = self.update_queue[-1]

                
                print('Fetching TXN data for %s/%s'%(symbol, amount))
                token = BancorNetworkToken.get(symbol=symbol)
                self.cache[(symbol, amount)] = get_txn_payload(token, amount*1e18)
                del self.update_queue[self.update_queue.index((symbol, amount))]

            except Exception as err:
                print('An error occued in the update worker')
                print(err)

    def is_txn_expired(self, raw_txn):
        """
        Check whether a transaction is expired
        """
        txn = TransactionLog.from_raw_txn(raw_txn, is_hex=True) 
        max_block = txn.get_inputs(contract=BANCOR_CONTRACT)[1]['_block']

        if max_block < (WEB3.eth.blockNumber + 100):
            return True
        return False

    def update_cache(self):
        """
        Update the values in the cache
        """
        for token in self.tokens:
            for amount in self.amounts:

                tk = (token.symbol, amount)

                if tk not in self.cache and tk not in self.update_queue:
                    self.update_queue.insert(0, tk)
                    continue

                if tk in self.cache and tk not in self.update_queue and self.is_txn_expired(self.cache[tk]):
                    del self.cache[tk]
                    self.update_queue.insert(0, tk)

    def update_current_gas_limit(self):
        """
        Update the current gas limit
        """
        new_gas_price = self.gas_limit_contract.call().gasPrice()

        if new_gas_price != self.current_gas_limit:
            print('Warning: New gas price detected.  Evicting cache')
            self.current_gas_limit = new_gas_price
            self.cache = {}

    def get_front_txn(self, token_symbol, amount):
        """
        Return a cached raw transaction or raise an error
        """
        try:
            tx = self.cache[(token_symbol,amount)]
            del self.cache[(token_symbol, amount)]
            return tx
        except KeyError:
            raise(Exception('Cached tx for %s/%s not found'%(token_symbol, amount)))

