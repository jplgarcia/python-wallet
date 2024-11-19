import json
from coil_wallet.log import logger
from coil_wallet.util import decode_payload, decode_id_val, encode_function_call, encode_values
from coil_wallet.balance import Balance
from coil_wallet.outputs import Notice, Voucher
from coil_wallet.token_processor import TokenProcessor

ERC20_TRANSFER_FUNCTION_SELECTOR = "transfer(address,uint256)"

class Erc20Processor(TokenProcessor):
    """Handles Ether-specific operations"""

    def __init__(self, vault:dict[str:Balance]):
        """
        Initialize the token processor with a reference to a Balance instance.

        Parameters:
            balance (Balance): An instance of the Balance class, which manages asset balances.
        """
        super().__init__(vault)

    def deposit(self, payload:str) -> Notice:
        account, erc20, amount = None, None, 0
        try:
            erc20 = "0x" + payload[2:42]
            account = "0x" + payload[42:82]
            amount = decode_payload(['uint256'], '0x' + payload[82:])[0]
        except Exception as error:
            raise ValueError(
                "Payload does not conform to ERC-20 transfer ABI") from error


        logger.info(f"'{amount} {erc20}' tokens deposited "
                    f"in account '{account}'")
        
        balance = self._balance_get(account)
        balance._erc20_increase(erc20, amount)

        notice_payload = {
            "type": "erc20_deposit",
            "content": {
                "address": account,
                "erc20": erc20,
                "amount": amount
            }
        }
        return Notice.from_json(notice_payload)

    def withdraw(self, rollup_address:str, account: str, erc20:str, amount:int) -> Voucher:
        balance = self._balance_get(account)
        balance._erc20_decrease(erc20, amount)

        transfer_payload = encode_function_call(ERC20_TRANSFER_FUNCTION_SELECTOR, ["address", "uint256"], [account, amount])

        logger.info(f"'{amount} {erc20}' tokens withdrawn from '{account}'")
        return Voucher.from_hex(erc20, transfer_payload)

    def transfer(self, from_account:str, to_account:str, erc20:str, amount:int) -> Notice:
        balance = self._balance_get(from_account)
        balance_to = self._balance_get(to_account)

        balance._erc20_decrease(erc20, amount)
        balance_to._erc20_increase(erc20, amount)

        notice_payload = {
            "type": "erc20_transfer",
            "content": {
                "from": from_account,
                "to": to_account,
                "erc20": erc20,
                "amount": amount
            }
        }
        logger.info(f"'{amount} {erc20}' tokens transferred from "
                    f"'{from_account}' to '{to_account}'")
        return Notice.from_json(notice_payload)