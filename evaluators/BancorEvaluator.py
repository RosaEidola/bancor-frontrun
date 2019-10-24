"""
Evalator for Bancor frontrunning strategy
Possibly add more evaluators for different markets if we find opportunity

DLF 2019
"""
from models import BancorNetworkToken, TransactionLog
from evaluators.BancorCache import BancorCache
from evaluators.bancor_api import get_txn_payload
from utils import contract_from_address, generic_erc20_contract
import settings

class BancorEvaluator(object):
    """
    Evaluate transactions on Bancor
    """
    bancor_cache = BancorCache()

    def __init__(self):
        """
        Initialize object and cache
        """
        pass
        #self.bancor_cache.start_update_worker(wait_on_complete=True)

    def max_tradeable_amount(self, Xt, L, P, min_return=None, txn_fee=0, fill_rate=0.30):
        """
        Whats the max amount we can trade?

        args:
        Xt -- target transaction amount in ETHER
        L -- initial liquidity depth in ETHER
        P -- initial price in ETHER / TOKEN
        min_return -- minimum tokens awarded to target after frontrun in TOKENS
        """
        if not min_return:
            min_return = Xt / (P * (1 + (.02 + (Xt / L))))


        mp = Xt / min_return
        r1 = (P*Xt + L*mp - (4*L**2*P**2 - 4*L**2*P*mp + L**2*mp**2 + 4*L*P**2*Xt + 2*L*P*Xt*mp + P**2*Xt**2)**(1/2))/(2*P)
        r2 = (P*Xt + L*mp + (4*L**2*P**2 - 4*L**2*P*mp + L**2*mp**2 + 4*L*P**2*Xt + 2*L*P*Xt*mp + P**2*Xt**2)**(1/2))/(2*P)
        max_amount = max(min(r1, r2) ,0)

        print(min_return, r1, r2)
        max_pnl = max_amount*( Xt / (L - max_amount)) - ((1 / fill_rate)*txn_fee + txn_fee)
            
        return max_amount, max_pnl


    def parse_txn(self, tx_hash, is_hash=True):
        """
        Given a transaction hash, figure out what ERC20 token the TXN is trading to,
        and other key features about the transaction

        args:
        tx_hash -- Return the end token for a given transaction hash
        """
        if is_hash:
            txn = settings.WEB3.eth.getTransaction(tx_hash)
        else:
            txn = tx_hash

        inputs = settings.BANCOR_CONTRACT.decode_function_input(txn['input'])
        end_token_addr = inputs[1]['_path'][-1]
        token_contract = generic_erc20_contract(end_token_addr)
        sym = token_contract.call().symbol()
        
        token = BancorNetworkToken.get(symbol=sym)
        token.token_addr = end_token_addr
        token.decimals = token_contract.call().decimals()
        txn = TransactionLog.from_raw_txn(txn, is_hex=True)
        txn.get_inputs(contract=settings.BANCOR_CONTRACT)
        
        return token, txn


    def update_min_return(self, target_txn, front_txn, sign=False):
        """
        Take a raw transaction and update the _minReturn argument 
        so be exactly what we would be awarded
        """
        inputs = target_txn.get_inputs()[1]

        # Update the raw transaction details:
        amt = int(settings.WEB3.eth.call(front_txn).hex(), 0)
        func = settings.BANCOR_CONTRACT.functions.quickConvertPrioritized(
                    inputs['_path'],
                    inputs['_amount'],
                    amt,#inputs['_minReturn'],
                    inputs['_block'],
                    inputs['_v'],
                    inputs['_r'],
                    inputs['_s'])
        updated_tx = func.buildTransaction({
                    'gas' : front_txn['gas'],
                    'from': front_txn['from'],
                    'value' : front_txn['value'],
                    'gasPrice' : front_txn['gasPrice'],
                    'nonce' : front_txn['nonce'],
                    'chainId':1 })

        # Sign the transaction locally for extra security:
        if sign:
            updated_tx = settings.WEB3.eth.account.signTransaction(updated_tx, private_key=settings.PRIVATE_KEY)

        return updated_tx



    def evaluate(self, txn):
        """
        Main evaulation method

        # 1 Determine token and transaction details from raw_txn
        # 2 Validate txn locally to make sure it actually runs
        # 3 Determine the max capacity for that trade
        # 4 Grab the frontrun txn details from the BancorTxnCache
        # 5 Run the transaction locally to set _minReturn variable
        # 6 Update frontrun txn to include _minReturn
        # 7 Check that gas price doesnt exceed our own / exp profit > 0
        # 8 Emit the transaction to the network!
        # 9 Save the txn_hash to the DB for tracking purposes
        """

        # Parse the target transaction and return the token its trading and a parsed transaction object:
        token, target_txn = self.parse_txn(txn, is_hash=False)

        # Determine the max amount we can trade on this amount:
        max_amt, est_pnl = self.max_tradeable_amount(target_txn.ether_value(), token.liquidity_depth, token.price)
        #assert(max_amt > 1e18)

        # TODO: Validate the target transaction to make sure it doesn't fail
        # dosomethinghere

        # Get the transaction from the cache for faster txn emission:
        #front_raw_txn = self.bancor_cache.get_front_txn(token.symbol, 1)
        front_raw_txn = get_txn_payload(token, 1e18)
        parsed_front_txn = TransactionLog.from_raw_txn(front_raw_txn, is_hex=True)

        # Check to make sure out front_run_txn doesnt have a lower gas price than the target:
        gps = (parsed_front_txn.gas_price, target_txn.gas_price)
        #assert gps[0] == gps[1], 'Gas prices dont match: %s / %s'%gps

        # Update the _minReturn parameter of the front_raw_txn:
        front_raw_txn = self.update_min_return(target_txn, front_raw_txn, sign=False)


        # Provide some logging info:
        delta = target_txn.ether_value() / (token.liquidity_depth - parsed_front_txn.ether_value())
        print("""
        Detected valid target transaction:
            Buying {0:.2f}E of {1} w/ slippage {2:.10f}
            Front Txn of {3:.3f}E w/ est_pnl of ${4:.2f}
        """.format(target_txn.ether_value(), token.symbol, delta, max_amt,
        270*(delta * max_amt)))

        # Send that shit to the market!!
        #sent_txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)

        # Save the trade to the DB:
        #trade = BancorTrade(txn_hash=sent_txn_hash)
        #trade.save()



