from eth_utils.conversions import to_hex
from eth_typing.evm import ChecksumAddress
from eth_utils import to_wei
import web3
from base import *
from config import config
import json
import names


def generateRandomGreeting():
    return names.get_full_name()


class Contract:

    def __init__(self, index) -> None:
        self.w3: web3.Web3
        self.account: web3.Account
        self.w3, self.account = init_web3_and_account(
            endpoint_name=KILN, private_key=config['PRIVATTE_KEY'])

        self.abi, self.bytecode = self.parseData()
        self.name = generateRandomGreeting()
        self.index = index
        self.address = ''

    def parseData(self):
        abi = []
        bytecode = ''
        with open('./Greeter.json', 'r') as f:
            data = json.load(fp=f)
            abi = data["abi"]
            bytecode = data["bytecode"]
            f.close()
        return abi, bytecode

    def deploy(self):
        receipt, ok = send(w3=self.w3,
                           account=self.account,
                           chain_id=to_hex(1337802),
                           gas=1000000,
                           gas_price=to_wei(10, 'gwei'),
                           data=self.bytecode)
        if receipt is None or ok == False:
            return None
        self.address = receipt['contractAddress']
        print(f'contract `Greeter` is deployed at address: {self.address}')

    def setGreeting(self):
        if self.address == None:
            return
        contract = init_contract(w3=self.w3,
                                 addr=self.address,
                                 dir='./',
                                 abi_name='Greeter_abi.json')
        new_greeting = generateRandomGreeting()
        f = contract.functions.setGreeting(new_greeting)
        print(f'setGreeting for {new_greeting}')
        send(w3=self.w3,
             account=self.account,
             f=f,
             gas=1000000,
             gas_price=to_wei(10, 'gwei'))


if __name__ == '__main__':
    # recommend 11
    contract_count = int(input('how many contracts do you want to deploy: '))
    interaction_count_per_contract = int(
        input(
            'how many interactions do you want to do for each contract you deployed: '
        ))

    while contract_count > 0:
        contract = Contract(contract_count)
        contract.deploy()
        interact_count = interaction_count_per_contract
        while interact_count > 0:
            contract.setGreeting()
            interact_count -= 1
        contract_count -= 1
