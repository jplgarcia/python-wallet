import json
from coil_wallet.log import logger
from coil_wallet.util import decode_payload, decode_id_val, encode_function_call, encode_values
from coil_wallet.balance import Balance
from coil_wallet.outputs import Notice, Voucher
from coil_wallet.token_processor import TokenProcessor
from typing import List, Tuple, Any


ERC1155_SAFE_TRANSFER_FROM_SELECTOR = "safeTransferFrom(address,address,uint256,uint256,bytes)"
ERC1155_SAFE_BATCH_TRANSFER_FROM_SELECTOR = "safeBatchTransferFrom(address,address,uint256[],uint256[],bytes)"

class Erc1155Processor(TokenProcessor):
    """Handles Ether-specific operations"""

    def __init__(self, vault:dict[str:Balance]):
        """
        Initialize the token processor with a reference to a Balance instance.

        Parameters:
            balance (Balance): An instance of the Balance class, which manages asset balances.
        """
        super().__init__(vault)

    def deposit(self, payload:str) -> Notice:
        token, account, token_id, value = None, None, None, None
        try:
            token = "0x" + payload[2:42]
            account = "0x" + payload[42:82]

            input_data = decode_payload(
                ['uint256',  # Token ID
                'uint256'], # Token amount (value)
                '0x' + payload[82:]
            )

            token_id = input_data[0]
            value = input_data[1]
        except Exception as error:
            raise ValueError("Payload does not conform to ERC-1155 single deposit ABI") from error
        
        logger.info(f"'{value} of token ID {token_id}' deposited "
                f"in account '{account}' via contract '{token}'")
        balance = self._balance_get(account)
        balance._erc1155_increase(token, token_id, value)

        notice_payload = {
            "type": "erc1155deposit",
            "content": {
                "address": account,
                "token": token,
                "token_id": token_id,
                "value": value
            }
        }
        return Notice.from_json(notice_payload)

    def withdraw(self, rollup_address:str, account:str, erc1155:str, token_id:int, amount:int) -> Voucher:
        if rollup_address == "":
            raise Exception("Dapp Relay not sent")

        balance = self._balance_get(account)
        balance._erc1155_decrease(erc1155, token_id, amount)

        transfer_payload = encode_function_call(ERC1155_SAFE_TRANSFER_FROM_SELECTOR, 
                                                ["address", "address", "uint256", "uint256", "bytes"],
                                                [rollup_address, account, token_id, amount, b''])

        logger.info(f"'{amount} of token {erc1155} ID {token_id}' withdrawn from '{account}'")
        return Voucher.from_hex(erc1155, transfer_payload)

    def transfer(self, from_account:str, to_account:str, erc1155:str, token_id:int, amount:int) -> Notice:
        balance = self._balance_get(from_account)
        balance_to = self._balance_get(to_account)

        balance._erc1155_decrease(erc1155, token_id, amount)
        balance_to._erc1155_increase(erc1155, token_id, amount)

        notice_payload = {
            "type": "erc1155transfer",
            "content": {
                "from": from_account,
                "to": to_account,
                "erc1155": erc1155,
                "token_id": token_id,
                "amount": amount
            }
        }
        logger.info(f"Token 'ERC-1155: {erc1155}, id: {token_id}, amount: {amount}' transferred from '{from_account}' to '{to_account}'")
        return Notice.from_json(notice_payload)
    
    def batch_deposit(self, payload:str) -> Notice:
        
        erc1155, account, token_ids, values = None, None, None, None
        try:
            erc1155 = "0x" + payload[2:42]
            account = "0x" + payload[42:82]
            data = payload[82:]

            # Decode tokenIds and values from the combined bytes
            main_structure = decode_payload(['uint256', 'uint256'], '0x' + data[:128])

            first_array_start = main_structure[0]*2
            second_array_start = main_structure[1]*2

            # Step 3: Decode the first array's length and elements
            first_array_length = decode_payload(['uint256'], '0x' + data[first_array_start:first_array_start+64])[0]
            first_array_elements = decode_payload(['uint256'] * first_array_length, '0x' + data[first_array_start+64:first_array_start+64+64*first_array_length])

            # Step 4: Decode the second array's length and elements
            second_array_length = decode_payload(['uint256'], '0x' + data[second_array_start:second_array_start+64])[0]
            second_array_elements = decode_payload(['uint256'] * second_array_length, '0x' + data[second_array_start+64:second_array_start+64+64*second_array_length])

            token_ids = first_array_elements
            values = second_array_elements

        except Exception as error:
            raise ValueError("Payload does not conform to ERC-1155 batch deposit ABI") from error
        
        logger.info(f"Batch deposit of tokens {token_ids} with values {values} "
                f"in account '{account}' via contract '{erc1155}'")
        
        balance = self._balance_get(account)
        for token_id, value in zip(token_ids, values):
            balance._erc1155_increase(erc1155, token_id, value)

        notice_payload = {
            "type": "erc1155b_atchdeposit",
            "content": {
                "address": account,
                "token": erc1155,
                "token_ids": token_ids,
                "values": values
            }
        }
        return Notice.from_json(notice_payload)
    
    def batch_withdraw(self, rollup_address:str, account:str, erc1155:str, token_ids:List[str], amounts:List[int]) -> Voucher:
        '''
        Withdraw ERC-1155 tokens in a batch transfer.

            Parameters:
                rollup_address (str): address of the contract dapp relay.
                sender (str): address of the token sender.
                token (str): ERC-1155 contract address.
                token_ids (list[int]): list of token IDs.
                values (list[int]): list of amounts of tokens to withdraw.
                data (bytes): additional data.

            Returns:
                voucher (Voucher): A voucher that calls the `safeBatchTransferFrom` function.
        '''
        if rollup_address == "":
            raise Exception("Dapp Relay not set")

        balance = self._balance_get(account)

        for token_id, amount in zip(token_ids, amounts):
            if amount < 0:
                raise ValueError(
                    f"Failed to decrease balance for ERC-1155 {erc1155}, token ID {token_id}. "
                    f"{amount} should be a positive number"
                )

            current_balance = balance._erc1155.get(erc1155, {}).get(token_id, 0)
            if current_balance < amount:
                raise ValueError(
                    f"Failed to decrease balance for ERC-1155 {erc1155}, token ID {token_id}. "
                    f"Not enough funds to decrease {amount}"
                )

        for token_id, value in zip(token_ids, amounts):
            balance._erc1155_decrease(erc1155, token_id, value)

        transfer_payload = encode_function_call(
            ERC1155_SAFE_BATCH_TRANSFER_FROM_SELECTOR,
            ["address", "address", "uint256[]", "uint256[]", "bytes"],
            [rollup_address, account, token_ids, amounts, b'']
        )

        logger.info(f"Batch withdraw of tokens {token_ids} with values {amount} from '{account}'")
        return Voucher.from_hex(erc1155, transfer_payload)
    
    def batch_transfer(self, from_account, to_account, erc1155, token_ids:List[str], amounts:List[int]) -> Notice:
        '''
        Transfer multiple ERC-1155 tokens from `account` to `to`.

            Parameters:
                account (str): address who owns the tokens.
                to (str): address to send tokens to.
                erc1155 (str): address of the ERC-1155 contract.
                token_ids (list[int]): list of token IDs to transfer.
                amounts (list[int]): list of amounts for each token ID.

            Returns:
                notice (Notice): A notice detailing the batch transfer operation.
        '''
        if len(token_ids) != len(amounts):
            raise ValueError("Token IDs and amounts must have the same length")

        balance = self._balance_get(from_account)
        balance_to = self._balance_get(to_account)

        # Guaranteeing atomicity, checking every balance before allowing transfers
        for token_id, amount in zip(token_ids, amounts):
            if amount < 0:
                raise ValueError(
                    f"Failed to decrease balance for ERC-1155 {erc1155}, token ID {token_id}. "
                    f"{amount} should be a positive number"
                )

            current_balance = balance._erc1155.get(erc1155, {}).get(token_id, 0)
            if current_balance < amount:
                raise ValueError(
                    f"Failed to decrease balance for ERC-1155 {erc1155}, token ID {token_id}. "
                    f"Not enough funds to decrease {amount}"
                )

        for token_id, amount in zip(token_ids, amounts):
            balance._erc1155_decrease(erc1155, token_id, amount)
            balance_to._erc1155_increase(erc1155, token_id, amount)

        notice_payload = {
            "type": "erc1155batchtransfer",
            "content": {
                "from": from_account,
                "to": to_account,
                "erc1155": erc1155,
                "token_ids": token_ids,
                "amounts": amounts
            }
        }
        logger.info(f"Batch tokens 'ERC-1155: {erc1155}' with ids '{token_ids}' and amounts '{amounts}' transferred from '{from_account}' to '{to_account}'")
        return Notice.from_json(notice_payload)