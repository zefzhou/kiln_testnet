from typing import Optional, Tuple
from eth_utils.conversions import to_hex
from web3.types import Wei, TxParams
from web3.contract import ContractFunction
from eth_typing.evm import Address
from web3 import Web3, Account
from pathlib import Path
import requests
from loguru import logger
import time

STATUS = 'status'
TRANSACTION_HASH = 'transactionHash'

nonces = {}

BSC = 'bsc'
BSC_TESTNET = 'bsc_testnet'
ETH = 'eth'
KOVAN = 'kovan'
GOERLI = 'goerli'
RINKEBY = 'rinkeby'
ROPSTEN = 'ropsten'
MATIC = 'matic'
MATIC_TESTNET = 'matic_testnet'
FANTOM_TESTNET = 'fantom_testnet'
AVAX_TESTNET = 'avax_testnet'
CHZ_TESTNET = 'chz_testnet'
KILN = 'kiln'

endpoints = {
    BSC: 'https://bsc-dataseed.binance.org/',
    BSC_TESTNET: 'https://data-seed-prebsc-1-s1.binance.org:8545/',
    ETH: 'https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161',
    KOVAN: 'https://kovan.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161',
    GOERLI: 'https://goerli.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161',
    RINKEBY: 'https://rinkeby.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161',
    ROPSTEN: 'https://ropsten.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161',
    MATIC: 'https://rpc-mainnet.maticvigil.com/',
    MATIC_TESTNET: 'https://matic-testnet-archive-rpc.bwarelabs.com/',
    FANTOM_TESTNET: 'https://rpc.testnet.fantom.network/',
    AVAX_TESTNET: 'https://api.avax-test.network/ext/bc/C/rpc',
    CHZ_TESTNET: 'https://scoville-rpc.chiliz.com',
    KILN: 'https://rpc.kiln.themerge.dev/'
}


def init_web3_and_account(endpoint_name: str,
                          endpoint: str = '',
                          private_key: str = '') -> Tuple:
    return init_web3(endpoint_name=endpoint_name,
                     endpoint=endpoint), init_account(private_key=private_key)


def init_web3(endpoint_name: str, endpoint: str) -> Web3:
    adapter = requests.adapters.HTTPAdapter(pool_connections=20,
                                            pool_maxsize=20,
                                            max_retries=1)
    session = requests.Session()
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    if endpoint_name in endpoints:
        endpoint = endpoints[endpoint_name]
    w3_provider = Web3.HTTPProvider(endpoint_uri=endpoint, session=session)
    return Web3(provider=w3_provider)


def init_account(private_key: str) -> Account:
    return Account.from_key(private_key)


def init_addr(addr: str):
    return Web3.toChecksumAddress(addr)


def init_contract(w3: Web3, addr: Address, dir: str, abi_name: str):
    with Path(dir).joinpath(abi_name).open('r') as f:
        abi = f.read()
        f.close()
        return w3.eth.contract(address=addr, abi=abi)


def get_nonce(w3: Web3, addr: Address, chain_id: str = None):
    return w3.eth.get_transaction_count(addr, 'pending')


def get_default_tx_params(w3: Web3,
                          account: Account,
                          chain_id: str = None,
                          to: Address = None,
                          data: str = None,
                          val: Wei = Wei(0),
                          gas: Wei = Wei(100000),
                          gas_price: Optional[Wei] = None):
    if gas_price is None:
        gas_price = w3.eth.gas_price
    tx_params: TxParams = {
        'from': account.address,
        'value': val,
        'gas': gas,
        'gasPrice': gas_price,
        'nonce': get_nonce(w3, account.address, chain_id)
    }
    if to is not None:
        tx_params['to'] = to
    if data is not None:
        tx_params['data'] = data
    if chain_id is not None:
        tx_params['chainId'] = chain_id
    return tx_params


def sign_tx(w3: Web3, params: TxParams, account: Account):
    return w3.eth.account.sign_transaction(params, private_key=account.key)


def send_tx_and_wait_recipt(w3: Web3, signed_tx, timeout: int = 120) -> Tuple:
    try:
        tx = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        txHash = to_hex(tx)
        recipt = w3.eth.wait_for_transaction_receipt(tx, timeout=timeout)
        if recipt == None:
            logger.error(f'tx failed: {txHash}')
            return None, False
        status = recipt[STATUS]
        if status != 0:
            logger.info(f'tx succeeded : {txHash}')
            return recipt, True
        else:
            logger.error(f'tx failed, check it: {txHash}')
            return recipt, False
    except Exception as e:
        logger.warning(f'tx failed : {e}')
        return None, False


def send(w3: Web3,
         account: Account,
         chain_id: str = None,
         f: ContractFunction = None,
         gas: Wei = Wei(100000),
         gas_price: Optional[Wei] = None,
         to: Address = None,
         data: str = None,
         val: Wei = Wei(0),
         timeout: int = 120):
    tx_params = get_default_tx_params(w3=w3,
                                      account=account,
                                      chain_id=chain_id,
                                      to=to,
                                      data=data,
                                      val=val,
                                      gas=gas,
                                      gas_price=gas_price)
    if f is not None:
        tx_params = f.buildTransaction(transaction=tx_params)
    signed_tx = sign_tx(w3=w3, account=account, params=tx_params)
    return send_tx_and_wait_recipt(w3=w3, signed_tx=signed_tx, timeout=timeout)


def deadline(t: int):
    return int(time.time()) + t
