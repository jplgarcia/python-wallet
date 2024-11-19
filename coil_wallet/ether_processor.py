import json
from coil_wallet.log import logger
from coil_wallet.util import decode_payload, decode_id_val, encode_function_call, encode_values
from coil_wallet.balance import Balance
from coil_wallet.outputs import Notice, Voucher
from coil_wallet.token_processor import TokenProcessor

class EtherProcessor(TokenProcessor):
    """Handles Ether-specific operations"""

    def __init__(self, vault:dict[str:Balance]):
        """
        Initialize the token processor with a reference to a Balance instance.

        Parameters:
            balance (Balance): An instance of the Balance class, which manages asset balances.
        """
        super().__init__(vault)

    def deposit(self, payload:str) -> Notice:
        account, amount = None, 0
        try:
            account = payload[0:42]
            amount = decode_payload(
                ['uint256'], # Amount of Ether being deposited
                '0x' + payload[42:]
            )[0]
        except Exception as error:
            raise ValueError(
                "Payload does not conform to Ether transfer ABI") from error

        balance = self._balance_get(account)
        balance._ether_increase(amount)

        notice_payload = {
            "type": "ether_deposit",
            "content": {
                "address": account,
                "amount": amount
            }
        }
        return Notice.from_json(notice_payload)

    def withdraw(self, rollup_address:str, account:str, amount:int) -> Voucher:
        if not rollup_address:
            raise ValueError("Rollup address not set")
        
        balance = self._balance_get(account)
        balance._ether_decrease(amount)
        value = '0x' + encode_values(["uint256"], [amount]).hex()
        logger.info(f"{amount} Ether withdrawn from {account}")
        return Voucher.from_hex(account, '0x', value)

    def transfer(self, from_account: str, to_account: str, amount: int) -> Notice:
        balance = self._balance_get(from_account)
        balance_to = self._balance_get(to_account)

        balance._ether_decrease(amount)
        balance_to._ether_increase(amount)

        logger.info(f"{amount} Ether transferred from {from_account} to {to_account}")
        return Notice.from_json({
            "type": "ether_transfer",
            "content": {"from": from_account, "to": to_account, "amount": amount}
        })