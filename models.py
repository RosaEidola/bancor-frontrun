from peewee import *
import datetime
import settings
from utils import contract_from_address


class BaseModel(Model):
    """
    Underlying database
    """

    class Meta:
        database = settings.DATABASE


class TransactionLog(BaseModel):
    """
    Transaction log model
    """
    block_hash = TextField()
    from_addr = TextField()
    gas = IntegerField()
    gas_price = IntegerField()
    txn_hash = TextField(primary_key=True)
    input_data = TextField()
    nonce = IntegerField()
    to_addr = TextField()
    txn_index = IntegerField(default=None)
    value = IntegerField(default=0)

    # Log level data:
    created_date = DateTimeField(default=datetime.datetime.now()) 
    detected_by = TextField()

    _parsed_inputs = None
    _contract = None

    @classmethod
    def from_raw_txn(cls, txn, is_hex=False):
        """
        Given a raw transaction, return a normalized TransactionLog object

        args:
        txn -- a dictionary-like object 
        is_hex -- are the values hex encoded?
        """
        conv = lambda x: settings.WEB3.toInt(hexstr=x) if is_hex else x
        return cls(block_hash=txn.get('blockHash', None),
                   from_addr=txn['from'],
                   gas=conv(txn['gas']),
                   gas_price=conv(txn['gasPrice']),
                   txn_hash=txn.get('hash', None),
                   input_data=txn.get('input', txn.get('data')),
                   nonce=conv(txn['nonce']),
                   to_addr=txn['to'],
                   value=conv(txn['value']))

    def get_contract(self, contract=None):
        """
        Return the contract interface of the to_address
        """
        if self._contract:
            return self._contract
        self._contract = contract if contract else contract_from_address(self.to_addr)  

        return self._contract

    def get_inputs(self, contract=None):
        """
        Parse the inputs according to the ABI. 

        args:
        contract -- Optional.  If included, no web request required
        """
        return self.get_contract(contract=contract).decode_function_input(self.input_data)

    def ether_value(self):
        """
        Returns value parameter in units of Ether
        """
        return float(settings.WEB3.fromWei(self.value, 'Ether'))


class BancorNetworkToken(BaseModel):
    """
    Store persistant data about tokens in Bancor Network
    """

    token_id = CharField(max_length=24)
    name = CharField(max_length=100)
    symbol = CharField(max_length=10, primary_key=True)
    price = FloatField(null=True)
    liquidity_depth = FloatField(null=True)
    volume = FloatField(default=0)
    can_trade = BooleanField(default=False)

    _address = None
    _decimals = None

    def __str__(self):
        """
        To string
        """
        return '{0}:{1}'.format(self.symbol, self.name)


class BancorTrade(BaseModel):
    """
    Keep track of trades we made so we can analyze / unwind them
    """

    txn_hash = TextField(primary_key=True)
    buy_sucess = BooleanField(default=False)
    sell_success = BooleanField(null=True, default=None)









