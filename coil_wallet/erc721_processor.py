import json
from coil_wallet.log import logger
from coil_wallet.util import decode_payload, decode_id_val, encode_function_call, encode_values
from coil_wallet.balance import Balance
from coil_wallet.outputs import Notice, Voucher
from coil_wallet.token_processor import TokenProcessor

ERC721_SAFE_TRANSFER_FROM_SELECTOR = "safeTransferFrom(address,address,uint256)"

class Erc721Processor(TokenProcessor):
    """Handles Ether-specific operations"""

    def __init__(self, vault: dict[str:Balance]):
        """
        Initialize the token processor with a reference to a Balance instance.

        Parameters:
            balance (Balance): An instance of the Balance class, which manages asset balances.
        """
        super().__init__(vault)

    def deposit(self, payload:str) -> Notice:
        erc721, account, token_id = None, None, None
        try:
            erc721 = "0x" + payload[2:42]
            account = "0x" + payload[42:82]
            token_id = decode_payload(['uint256'], '0x' + payload[82:])[0]

        except Exception as error:
            raise ValueError(
                "Payload does not conform to ERC-721 transfer ABI") from error  
        
        logger.info(f"Token 'ERC-721: {erc721}, id: {token_id}' deposited "
                f"in '{account}'")
        
        balance = self._balance_get(account)
        balance._erc721_add(erc721, token_id)

        notice_payload = {
            "type": "erc721deposit",
            "content": {
                "address": account,
                "erc721": erc721,
                "token_id": token_id
            }
        }
        return Notice.from_json(notice_payload)
        

    def withdraw(self, rollup_address:str, account:str, erc721:str, token_id:int) -> Voucher:
        if rollup_address == "":
            raise Exception("Dapp Relay not set")
        
        balance = self._balance_get(account)
        balance._erc721_remove(erc721, token_id)

        logger.info(f"Token 'ERC-721: {erc721}, id: {token_id}' withdrawn "
                    f"from '{account}'")
        return Voucher.from_function_selector(erc721, 
                                              ERC721_SAFE_TRANSFER_FROM_SELECTOR, 
                                              ["address", "address", "uint256"], 
                                              [rollup_address, account, token_id])

    def transfer(self, from_account:str, to_account:str, erc721:str, token_id:int) -> Notice:
        balance = self._balance_get(from_account)
        balance_to = self._balance_get(to_account)

        balance._erc721_remove(erc721, token_id)
        balance_to._erc721_add(erc721, token_id)

        notice_payload = {
            "type": "erc721transfer",
            "content": {
                "from": from_account,
                "to": to_account,
                "erc721": erc721,
                "token_id": token_id
            }
        }
        logger.info(f"Token 'ERC-721: {erc721}, id: {token_id}' transferred "
                    f"from '{from_account}' to '{to_account}'")
        return Notice.from_json(notice_payload)