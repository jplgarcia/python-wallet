# Copyright 2022 Cartesi Pte. Ltd.
#
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License. You may obtain a copy of the
# License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

import json
from coil_wallet.util import decode_payload, decode_id_val, encode_function_call, encode_values
from coil_wallet.balance import Balance
from coil_wallet.log import logger
from coil_wallet.outputs import Notice, Voucher

ETHER_TRANSFER_FUNCTION_SELECTOR = "withdrawEther(address,uint256)"
ERC20_TRANSFER_FUNCTION_SELECTOR = "transfer(address,uint256)"
ERC721_SAFE_TRANSFER_FROM_SELECTOR = "safeTransferFrom(address,address,uint256)"
ERC1155_SAFE_TRANSFER_FROM_SELECTOR = "safeTransferFrom(address,address,uint256,uint256,bytes)"
ERC1155_SAFE_BATCH_TRANSFER_FROM_SELECTOR = "safeBatchTransferFrom(address,address,uint256[],uint256[],bytes)"

_accounts = dict[str: Balance]()

def _balance_get(account) -> Balance:
    balance = _accounts.get(account)

    if not balance:
        _accounts[account] = Balance(account)
        balance = _accounts[account]

    return balance

def balance_get(account) -> Balance:
    """Retrieve the balance of all Ether, ERC-20 and ERC-721 tokens for `account`"""

    logger.info(f"Balance for '{account}' retrieved")
    return _balance_get(account)


def ether_deposit_process(payload: str):
    '''
        Process the ABI-encoded input data sent by the EtherPortal
        after an Ether deposit
            Parameters:
                payload (str): the binary input data as hex string.

            Returns:
                notice (Notice): A notice whose payload is the hex value for an Ether deposit JSON.
                report (Error): A report detailing the operation's failure reason.
    '''
    # remove the '0x' prefix and convert to bytes
    account, amount = _ether_deposit_parse(payload)
    logger.info(f"'{amount} ' ether deposited "
                f"in account '{account}'")
    return _ether_deposit(account, amount)

def _ether_deposit_parse(payload: str):
    '''
    Retrieve the ABI-encoded input data sent by the EtherPortal
    after an Ether deposit.

        Parameters:
            payload (str): hex of ABI-encoded input

        Returns:
            A tuple containing:
                account (str): address which owns the tokens
                amount (int): amount of deposited ERC-20 tokens
    '''
    try:
        account = payload[0:42]
        amount = decode_payload(
            ['uint256'], # Amount of Ether being deposited
            '0x' + payload[42:]
        )[0]
        return account, amount
    except Exception as error:
        raise ValueError(
            "Payload does not conform to Ether transfer ABI") from error

def _ether_deposit(account, amount):
    '''
    Deposit Ether in account.

        Parameters:
            account (str): address who owns the tokens.
            amount (float): amount of tokens to deposit.

        Returns:
            notice (Notice): A notice whose payload is the hex value for an
            Ether deposit JSON.
    '''
    balance = _balance_get(account)
    balance._ether_increase(amount)

    notice_payload = {
        "type": "etherdeposit",
        "content": {
            "address": account,
            "amount": amount
        }
    }
    return Notice(json.dumps(notice_payload))

def ether_withdraw(rollup_address, account, amount):
    '''
    Extract Ether from account.

        Parameters:
            rollup_address (str): address of the contract dapp relay.
            account (str): address who owns the tokens.
            amount (float): amount of tokens to withdraw.

        Returns:
            voucher (Voucher): A voucher that transfers `amount` tokens to
            `account` address.
    '''
    if rollup_address == "":
        raise Exception("Dapp Relay not set")

    balance = _balance_get(account)
    balance._ether_decrease(amount)


    logger.info(f"'{amount}' tokens withdrawn from '{account}'")

    value = '0x' + encode_values(["uint256"], [amount]).hex()
    print("\n\n encoded params")
    print(value)
    return Voucher(account, "0x", value)

def ether_transfer(account, to, amount):
    '''
    Transfer Ether from `account` to `to`.

        Parameters:
            account (str): address who owns the tokens.
            to (str): address to send tokens to.
            amount (int): amount of tokens to transfer.

        Returns:
            notice (Notice): A notice detailing the transfer operation.
    '''
    balance = _balance_get(account)
    balance_to = _balance_get(to)

    balance._ether_decrease(amount)
    balance_to._ether_increase(amount)

    notice_payload = {
        "type": "erthertransfer",
        "content": {
            "from": account,
            "to": to,
            "amount": amount
        }
    }
    logger.info(f"'{amount}' tokens transferred from "
                f"'{account}' to '{to}'")
    return Notice(json.dumps(notice_payload))  

def erc20_deposit_process(payload:str):
    '''
    Process the ABI-encoded input data sent by the ERC20Portal
    after an ERC-20 deposit
        Parameters:
            payload (str): the binary input data as hex string.

        Returns:
            notice (Notice): A notice whose payload is the hex value for an ERC-20 deposit JSON.
            report (Error): A report detailing the operation's failure reason.
    '''
    # remove the '0x' prefix and convert to bytes
    account, erc20, amount = _erc20_deposit_parse(payload)
    logger.info(f"'{amount} {erc20}' tokens deposited "
                f"in account '{account}'")
    return _erc20_deposit(account, erc20, amount)

def _erc20_deposit_parse(payload: str):
    '''
    Retrieve the ABI-encoded input data sent by the ERC20Portal
    after an ERC-20 deposit.

        Parameters:
            payload (str): hex of ABI-encoded input

        Returns:
            A tuple containing:
                account (str): address which owns the tokens
                erc20 (str): ERC-20 contract address
                amount (int): amount of deposited ERC-20 tokens
    '''
    try:
        # input_data = decode_payload(
        #     ['address',  # Address of the ERC-20 contract
        #      'address',  # Address which deposited the tokens
        #      'uint256'], # Amount of ERC-20 tokens being deposited
        #     payload
        # )

        erc20 = "0x" + payload[2:42]
        account = "0x" + payload[42:82]
        amount = decode_payload(['uint256'], '0x' + payload[82:])[0]
        return account, erc20, amount
    except Exception as error:
        raise ValueError(
            "Payload does not conform to ERC-20 transfer ABI") from error

def _erc20_deposit(account, erc20, amount):
    '''
    Deposit ERC-20 tokens in account.

        Parameters:
            account (str): address who owns the tokens.
            erc20 (str): address of the ERC-20 contract.
            amount (float): amount of tokens to deposit.

        Returns:
            notice (Notice): A notice whose payload is the hex value for an
            ERC-20 deposit JSON.
    '''
    balance = _balance_get(account)
    balance._erc20_increase(erc20, amount)

    notice_payload = {
        "type": "erc20deposit",
        "content": {
            "address": account,
            "erc20": erc20,
            "amount": amount
        }
    }
    return Notice(json.dumps(notice_payload))

def erc20_withdraw(account, erc20, amount):
    '''
    Extract ERC-20 tokens from account.

        Parameters:
            account (str): address who owns the tokens.
            erc20 (str): address of the ERC-20 contract.
            amount (float): amount of tokens to withdraw.

        Returns:
            voucher (Voucher): A voucher that transfers `amount` tokens to
            `account` address.
    '''
    balance = _balance_get(account)
    balance._erc20_decrease(erc20, amount)

    transfer_payload = encode_function_call(ERC20_TRANSFER_FUNCTION_SELECTOR, ["address", "uint256"], [account, amount])

    logger.info(f"'{amount} {erc20}' tokens withdrawn from '{account}'")
    return Voucher(erc20, transfer_payload)

def erc20_transfer(account, to, erc20, amount):
    '''
    Transfer ERC-20 tokens from `account` to `to`.

        Parameters:
            account (str): address who owns the tokens.
            to (str): address to send tokens to.
            erc20 (str): address of the ERC-20 contract.
            amount (int): amount of tokens to transfer.

        Returns:
            notice (Notice): A notice detailing the transfer operation.
    '''
    balance = _balance_get(account)
    balance_to = _balance_get(to)

    balance._erc20_decrease(erc20, amount)
    balance_to._erc20_increase(erc20, amount)

    notice_payload = {
        "type": "erc20transfer",
        "content": {
            "from": account,
            "to": to,
            "erc20": erc20,
            "amount": amount
        }
    }
    logger.info(f"'{amount} {erc20}' tokens transferred from "
                f"'{account}' to '{to}'")
    return Notice(json.dumps(notice_payload))


def erc721_deposit_process(payload:str):
    '''
    Process the ABI-encoded input data sent by the ERC721Portal
    after an ERC-721 deposit
        Parameters:
            payload (str): the binary input data as hex string.

        Returns:
            notice (Notice): A notice whose payload is the hex value for an
            ERC-721 deposit JSON.
            report (Error): A report detailing the operation's failure reason.
    '''
    # remove the '0x' prefix and convert to bytes
    account, erc721, token_id = _erc721_deposit_parse(payload)
    logger.info(f"Token 'ERC-721: {erc721}, id: {token_id}' deposited "
                f"in '{account}'")
    return _erc721_deposit(account, erc721, token_id)

def _erc721_deposit_parse(payload: str):
    '''
    Retrieve the ABI-encoded input data sent by the Portal
    after an ERC-721 deposit.

        Parameters:
            payload (str): hex of ABI-encoded input

        Returns:
            A tuple containing:
                account (str): address of the ERC-721 token owner
                erc721 (str): ERC-721 contract address
                token_id (int): ERC-721 token ID
    '''
    try:
        erc721 = "0x" + payload[2:42]
        account = "0x" + payload[42:82]
        token_id = decode_payload(['uint256'], '0x' + payload[82:])[0]

        return account, erc721, token_id
    except Exception as error:
        raise ValueError(
            "Payload does not conform to ERC-721 transfer ABI") from error
    
def _erc721_deposit(account, erc721, token_id):
    '''
    Deposit the ERC-721 token in account

        Parameters:
            account (str): address of the ERC-721 token owner
            erc721 (str): ERC-721 contract address
            token_id (int): ERC-721 token ID

        Returns:
            notice (Notice): A notice whose payload is the hex value for an
            ERC-721 deposit JSON
    '''
    balance = _balance_get(account)
    balance._erc721_add(erc721, token_id)

    notice_payload = {
        "type": "erc721deposit",
        "content": {
            "address": account,
            "erc721": erc721,
            "token_id": token_id
        }
    }
    return Notice(json.dumps(notice_payload))

def erc721_withdraw(rollup_address, sender, erc721, token_id):

    if rollup_address == "":
        raise Exception("Dapp Relay not set")
    
    balance = _balance_get(sender)
    balance._erc721_remove(erc721, token_id)
   

    payload = encode_function_call(ERC721_SAFE_TRANSFER_FROM_SELECTOR, ["address", "address", "uint256"], [rollup_address, sender, token_id])

    logger.info(f"Token 'ERC-721: {erc721}, id: {token_id}' withdrawn "
                f"from '{sender}'")
    return Voucher(erc721, payload)

def erc721_transfer(account, to, erc721, token_id):
    '''
    Transfer a ERC-721 token from `account` to `to`.

        Parameters:
            account (str): address who owns the token.
            to (str): address to send token to.
            erc721 (str): address of the ERC-721 contract.
            token_id (int): the ID of the token being transfered.

        Returns:
            notice (Notice): A notice detailing the transfer operation.
    '''
    balance = _balance_get(account)
    balance_to = _balance_get(to)

    balance._erc721_remove(erc721, token_id)
    balance_to._erc721_add(erc721, token_id)

    notice_payload = {
        "type": "erc721transfer",
        "content": {
            "from": account,
            "to": to,
            "erc721": erc721,
            "token_id": token_id
        }
    }
    logger.info(f"Token 'ERC-721: {erc721}, id: {token_id}' transferred "
                f"from '{account}' to '{to}'")
    return Notice(json.dumps(notice_payload))


def erc1155_single_deposit_process(payload: str):
    '''
    Process the ABI-encoded input data sent by the ERC1155Portal after an ERC-1155 single deposit.

        Parameters:
            payload (str): the binary input data as hex string.

        Returns:
            notice (Notice): A notice whose payload is the hex value for an ERC-1155 deposit JSON.
            report (Error): A report detailing the operation's failure reason.
    '''
    token, sender, token_id, value = _erc1155_single_deposit_parse(payload)

    logger.info(f"'{value} of token ID {token_id}' deposited "
                f"in account '{sender}' via contract '{token}'")
    return _erc1155_deposit(sender, token, token_id, value)

def _erc1155_single_deposit_parse(payload: str):
    '''
    Retrieve the ABI-encoded input data sent by the ERC1155Portal after an ERC-1155 single deposit.

        Parameters:
            payload (str): hex of ABI-encoded input

        Returns:
            A tuple containing:
                token (str): ERC-1155 contract address.
                sender (str): address of the sender.
                token_id (int): token ID being deposited.
                value (int): amount of tokens being deposited.
    '''
    try:
        token = "0x" + payload[2:42]
        sender = "0x" + payload[42:82]

        input_data = decode_payload(
            ['uint256',  # Token ID
             'uint256'], # Token amount (value)
            '0x' + payload[82:]
        )

        token_id = input_data[0]
        value = input_data[1]

        return token, sender, token_id, value
    except Exception as error:
        raise ValueError("Payload does not conform to ERC-1155 single deposit ABI") from error

def _erc1155_deposit(account, token, token_id, value):
    '''
    Deposit ERC-1155 tokens in account.

        Parameters:
            account (str): address who owns the tokens.
            token (str): ERC-1155 contract address.
            token_id (int): token ID.
            value (int): amount of tokens to deposit.

        Returns:
            notice (Notice): A notice whose payload is the hex value for an ERC-1155 deposit JSON.
    '''
    balance = _balance_get(account)
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
    return Notice(json.dumps(notice_payload))

def erc1155_single_withdraw(rollup_address, sender, token, token_id, value):
    '''
    Withdraw ERC-1155 tokens in a single transfer.

        Parameters:
            rollup_address (str): address of the contract dapp relay.
            sender (str): address of the token sender.
            token (str): ERC-1155 contract address.
            token_id (int): token ID.
            value (int): amount of tokens to withdraw.
            data (bytes): additional data.

        Returns:
            voucher (Voucher): A voucher that calls the `safeTransferFrom` function.
    '''
    if rollup_address == "":
        raise Exception("Dapp Relay not set")

    balance = _balance_get(sender)
    balance._erc1155_decrease(token, token_id, value)

    transfer_payload = encode_function_call(ERC1155_SAFE_TRANSFER_FROM_SELECTOR, 
                                            ["address", "address", "uint256", "uint256", "bytes"],
                                            [rollup_address, sender, token_id, value, b''])

    logger.info(f"'{value} of token ID {token_id}' withdrawn from '{sender}'")
    return Voucher(token, transfer_payload)

def erc1155_transfer(account, to, erc1155, token_id, amount):
    '''
    Transfer ERC-1155 tokens from `account` to `to`.

        Parameters:
            account (str): address who owns the tokens.
            to (str): address to send tokens to.
            erc1155 (str): address of the ERC-1155 contract.
            token_id (int): the ID of the token being transferred.
            amount (int): amount of tokens to transfer.

        Returns:
            notice (Notice): A notice detailing the transfer operation.
    '''
    balance = _balance_get(account)
    balance_to = _balance_get(to)

    balance._erc1155_decrease(erc1155, token_id, amount)
    balance_to._erc1155_increase(erc1155, token_id, amount)

    notice_payload = {
        "type": "erc1155transfer",
        "content": {
            "from": account,
            "to": to,
            "erc1155": erc1155,
            "token_id": token_id,
            "amount": amount
        }
    }
    logger.info(f"Token 'ERC-1155: {erc1155}, id: {token_id}, amount: {amount}' transferred from '{account}' to '{to}'")
    return Notice(json.dumps(notice_payload))


def erc1155_batch_deposit_process(payload: str):
    '''
    Process the ABI-encoded input data sent by the ERC1155Portal after an ERC-1155 batch deposit.

        Parameters:
            payload (str): the binary input data as hex string.

        Returns:
            notice (Notice): A notice whose payload is the hex value for an ERC-1155 deposit JSON.
            report (Error): A report detailing the operation's failure reason.
    '''
    token, sender, token_ids, values = _erc1155_batch_deposit_parse(payload)
    logger.info(f"Batch deposit of tokens {token_ids} with values {values} "
                f"in account '{sender}' via contract '{token}'")
    return _erc1155_batch_deposit(sender, token, token_ids, values)

def _erc1155_batch_deposit_parse(payload: str):
    '''
    Retrieve the ABI-encoded input data sent by the ERC1155Portal after an ERC-1155 batch deposit.

        Parameters:
            payload (str): hex of ABI-encoded input

        Returns:
            A tuple containing:
                token (str): ERC-1155 contract address.
                sender (str): address of the sender.
                token_ids (list[int]): list of token IDs being deposited.
                values (list[int]): list of amounts of tokens being deposited.
    '''
    try:
        token = "0x" + payload[2:42]
        sender = "0x" + payload[42:82]
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

        return token, sender, token_ids, values
    except Exception as error:
        raise ValueError("Payload does not conform to ERC-1155 batch deposit ABI") from error

def _erc1155_batch_deposit(account, token, token_ids, values):
    '''
    Deposit ERC-1155 tokens in batch.

        Parameters:
            account (str): address who owns the tokens.
            token (str): ERC-1155 contract address.
            token_ids (list[int]): list of token IDs.
            values (list[int]): list of amounts of tokens to deposit.

        Returns:
            notice (Notice): A notice whose payload is the hex value for an ERC-1155 deposit JSON.
    '''
    balance = _balance_get(account)
    for token_id, value in zip(token_ids, values):
        balance._erc1155_increase(token, token_id, value)

    notice_payload = {
        "type": "erc1155batchdeposit",
        "content": {
            "address": account,
            "token": token,
            "token_ids": token_ids,
            "values": values
        }
    }
    return Notice(json.dumps(notice_payload))

def erc1155_batch_withdraw(rollup_address, sender, token, token_ids, values):
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

    balance = _balance_get(sender)
    for token_id, value in zip(token_ids, values):
        balance._erc1155_decrease(token, token_id, value)

    transfer_payload = encode_function_call(
        ERC1155_SAFE_BATCH_TRANSFER_FROM_SELECTOR,
        ["address", "address", "uint256[]", "uint256[]", "bytes"],
        [rollup_address, sender, token_ids, values, b'']
    )

    logger.info(f"Batch withdraw of tokens {token_ids} with values {values} from '{sender}'")
    return Voucher(token, transfer_payload)

def erc1155_batch_transfer(account, to, erc1155, token_ids, amounts):
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

    balance = _balance_get(account)
    balance_to = _balance_get(to)

    for token_id, amount in zip(token_ids, amounts):
        balance._erc1155_decrease(erc1155, token_id, amount)
        balance_to._erc1155_increase(erc1155, token_id, amount)

    notice_payload = {
        "type": "erc1155batchtransfer",
        "content": {
            "from": account,
            "to": to,
            "erc1155": erc1155,
            "token_ids": token_ids,
            "amounts": amounts
        }
    }
    logger.info(f"Batch tokens 'ERC-1155: {erc1155}' with ids '{token_ids}' and amounts '{amounts}' transferred from '{account}' to '{to}'")
    return Notice(json.dumps(notice_payload))
