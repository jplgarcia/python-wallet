import time
import json
import requests
from conftest import send_transaction, check_balance

ROLLUP_SERVER = "http://localhost:8080"
SLEEP_TIME = 5


def test_deposit_erc1155(web3_instance, accounts, portals, dapp_addresses, tokens):
    """
    Test depositing a single ERC1155 token into the dApp.
    """
    erc1155_address = tokens["erc1155"]
    token_id = 1
    value = 5

    # Approve the ERC1155 portal to transfer the token
    approve_data = web3_instance.to_hex(web3_instance.keccak(text="setApprovalForAll(address,bool)")[:4])
    encoded_data = web3_instance.codec.encode(["address", "bool"], [portals["erc1155"], True])
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_1"],
        accounts["private_key_1"],
        erc1155_address,
        approve_data + encoded_data.hex()
    )
    assert tx_hash, "ERC1155 token approval failed"
    time.sleep(SLEEP_TIME)

    # Deposit ERC1155 token
    deposit_data = web3_instance.to_hex(
        web3_instance.keccak(text="depositSingleERC1155Token(address,address,uint256,uint256,bytes,bytes)")[:4]
    )
    encoded_data = web3_instance.codec.encode(
        ["address", "address", "uint256", "uint256", "bytes", "bytes"],
        [erc1155_address, dapp_addresses["dapp_address"], token_id, value, b"", b""],
    )
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_1"],
        accounts["private_key_1"],
        portals["erc1155"],
        deposit_data + encoded_data.hex()
    )
    assert tx_hash, "ERC1155 single token deposit failed"
    time.sleep(SLEEP_TIME)

    # Verify balance after deposit
    balance = check_balance(
        "erc1155", accounts["account_1"], dapp_addresses["dapp_address"], token_address=erc1155_address, token_id=token_id
    )
    assert balance.get("amount") == value, f"Expected {value}, got {balance.get('amount')}"


def test_transfer_erc1155(web3_instance, accounts, dapp_addresses, tokens):
    """
    Test transferring a single ERC1155 token from account_1 to account_2 via the dApp.
    """
    erc1155_address = tokens["erc1155"]
    token_id = 1
    value = 3

    transfer_data = {
        "route": "erc1155_transfer",
        "args": {
            "from": accounts["account_1"],
            "to": accounts["account_2"],
            "erc1155": erc1155_address,
            "token_id": token_id,
            "amount": value,
        },
    }
    encoded_data = web3_instance.to_hex(web3_instance.keccak(text="addInput(address,bytes)")[:4])
    encoded_input = web3_instance.codec.encode(
        ["address", "bytes"],
        [dapp_addresses["dapp_address"], web3_instance.to_bytes(text=json.dumps(transfer_data))],
    )
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_1"],
        accounts["private_key_1"],
        dapp_addresses["input_box_address"],
        encoded_data + encoded_input.hex()
    )
    assert tx_hash, "ERC1155 single token transfer failed"
    time.sleep(SLEEP_TIME)

    # Verify balances after transfer
    sender_balance = check_balance(
        "erc1155", accounts["account_1"], dapp_addresses["dapp_address"], token_address=erc1155_address, token_id=token_id
    )
    receiver_balance = check_balance(
        "erc1155", accounts["account_2"], dapp_addresses["dapp_address"], token_address=erc1155_address, token_id=token_id
    )
    assert sender_balance.get("amount") == 2, f"Expected 5, got {sender_balance.get('amount')}"
    assert receiver_balance.get("amount") == 3, f"Expected {value}, got {receiver_balance.get('amount')}"

def test_withdraw_erc1155(web3_instance, accounts, dapp_addresses, tokens):
    """
    Test withdrawing a single ERC1155 token from the dApp to account_2.
    """
    erc1155_address = tokens["erc1155"]
    token_id = 1
    value = 3

    withdraw_data = {
        "route": "erc1155_withdraw",
        "args": {
            "from": accounts["account_2"],
            "erc1155": erc1155_address,
            "token_id": token_id,
            "amount": value,
        },
    }
    encoded_data = web3_instance.to_hex(web3_instance.keccak(text="addInput(address,bytes)")[:4])
    encoded_input = web3_instance.codec.encode(
        ["address", "bytes"],
        [dapp_addresses["dapp_address"], web3_instance.to_bytes(text=json.dumps(withdraw_data))],
    )
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_2"],
        accounts["private_key_2"],
        dapp_addresses["input_box_address"],
        encoded_data + encoded_input.hex()
    )
    assert tx_hash, "ERC1155 single token withdrawal failed"
    time.sleep(SLEEP_TIME)

    # Verify balance after withdrawal
    receiver_balance = check_balance(
        "erc1155", accounts["account_2"], dapp_addresses["dapp_address"], token_address=erc1155_address, token_id=token_id
    )
    assert receiver_balance.get("amount") == 0, f"Expected 0 for token ID {token_id}, got {receiver_balance.get('amount')}"


def test_deposit_erc1155_batch(web3_instance, accounts, portals, dapp_addresses, tokens):
    """
    Test depositing multiple ERC1155 tokens into the dApp in a batch.
    """
    erc1155_address = tokens["erc1155"]
    token_ids = [1, 2]
    values = [5, 5]

    # Approve the ERC1155 portal to transfer the tokens
    approve_data = web3_instance.to_hex(web3_instance.keccak(text="setApprovalForAll(address,bool)")[:4])
    encoded_data = web3_instance.codec.encode(["address", "bool"], [portals["erc1155_batch"], True])
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_1"],
        accounts["private_key_1"],
        erc1155_address,
        approve_data + encoded_data.hex()
    )
    assert tx_hash, "ERC1155 token approval failed"
    time.sleep(SLEEP_TIME)

    # Deposit ERC1155 tokens in a batch
    deposit_data = web3_instance.to_hex(
        web3_instance.keccak(text="depositBatchERC1155Token(address,address,uint256[],uint256[],bytes,bytes)")[:4]
    )
    encoded_data = web3_instance.codec.encode(
        ["address", "address", "uint256[]", "uint256[]", "bytes", "bytes"],
        [erc1155_address, dapp_addresses["dapp_address"], token_ids, values, b"", b""],
    )
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_1"],
        accounts["private_key_1"],
        portals["erc1155_batch"],
        deposit_data + encoded_data.hex()
    )
    assert tx_hash, "ERC1155 batch deposit failed"
    time.sleep(SLEEP_TIME)

    # Verify balances after batch deposit
    balance = check_balance(
        "erc1155", accounts["account_1"], dapp_addresses["dapp_address"], token_address=erc1155_address, token_id=1
    )
    assert balance.get("amount") == 7, f"Expected {7} for token ID {1}, got {balance.get('amount')}"
    
    balance = check_balance(
        "erc1155", accounts["account_1"], dapp_addresses["dapp_address"], token_address=erc1155_address, token_id=2
    )
    assert balance.get("amount") == 5, f"Expected {5} for token ID {2}, got {balance.get('amount')}"

def test_transfer_erc1155_batch(web3_instance, accounts, dapp_addresses, tokens):
    """
    Test transferring multiple ERC1155 tokens from account_1 to account_2 in a batch via the dApp.
    """
    erc1155_address = tokens["erc1155"]
    token_ids = [1, 2]
    values = [7, 4]

    transfer_data = {
        "route": "erc1155_batch_transfer",
        "args": {
            "from": accounts["account_1"],
            "to": accounts["account_2"],
            "erc1155": erc1155_address,
            "token_ids": token_ids,
            "amounts": values,
        },
    }
    encoded_data = web3_instance.to_hex(web3_instance.keccak(text="addInput(address,bytes)")[:4])
    encoded_input = web3_instance.codec.encode(
        ["address", "bytes"],
        [dapp_addresses["dapp_address"], web3_instance.to_bytes(text=json.dumps(transfer_data))],
    )
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_1"],
        accounts["private_key_1"],
        dapp_addresses["input_box_address"],
        encoded_data + encoded_input.hex()
    )
    assert tx_hash, "ERC1155 batch transfer failed"
    time.sleep(SLEEP_TIME)

    # Verify balances after batch transfer
    sender_balance = check_balance(
        "erc1155", accounts["account_1"], dapp_addresses["dapp_address"], token_address=erc1155_address, token_id=1
    )
    receiver_balance = check_balance(
        "erc1155", accounts["account_2"], dapp_addresses["dapp_address"], token_address=erc1155_address, token_id=1
    )
    assert sender_balance.get("amount") == 0, f"Expected 0 for token ID {1}, got {sender_balance.get('amount')}"
    assert receiver_balance.get("amount") == 7, f"Expected {7} for token ID {1}, got {receiver_balance.get('amount')}"

    sender_balance = check_balance(
        "erc1155", accounts["account_1"], dapp_addresses["dapp_address"], token_address=erc1155_address, token_id=2
    )
    receiver_balance = check_balance(
        "erc1155", accounts["account_2"], dapp_addresses["dapp_address"], token_address=erc1155_address, token_id=2
    )
    assert sender_balance.get("amount") == 1, f"Expected {1} for token ID {2}, got {sender_balance.get('amount')}"
    assert receiver_balance.get("amount") == 4, f"Expected {4} for token ID {2}, got {receiver_balance.get('amount')}"


def test_withdraw_erc1155_batch(web3_instance, accounts, dapp_addresses, tokens):
    """
    Test withdrawing multiple ERC1155 tokens from the dApp to account_2 in a batch.
    """
    erc1155_address = tokens["erc1155"]
    token_ids = [1, 2]
    values = [6, 4]

    withdraw_data = {
        "route": "erc1155_batch_withdraw",
        "args": {
            "from": accounts["account_2"],
            "erc1155": erc1155_address,
            "token_ids": token_ids,
            "amounts": values,
        },
    }
    encoded_data = web3_instance.to_hex(web3_instance.keccak(text="addInput(address,bytes)")[:4])
    encoded_input = web3_instance.codec.encode(
        ["address", "bytes"],
        [dapp_addresses["dapp_address"], web3_instance.to_bytes(text=json.dumps(withdraw_data))],
    )
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_2"],
        accounts["private_key_2"],
        dapp_addresses["input_box_address"],
        encoded_data + encoded_input.hex()
    )
    assert tx_hash, "ERC1155 batch withdrawal failed"
    time.sleep(SLEEP_TIME)

    # Verify balances after batch withdrawal
    receiver_balance = check_balance(
        "erc1155", accounts["account_2"], dapp_addresses["dapp_address"], token_address=erc1155_address, token_id=1
    )
    assert receiver_balance.get("amount") == 1, f"Expected {1} for token ID {1}, got {receiver_balance.get('amount')}"

    receiver_balance = check_balance(
        "erc1155", accounts["account_2"], dapp_addresses["dapp_address"], token_address=erc1155_address, token_id=2
    )
    assert receiver_balance.get("amount") == 0, f"Expected {6} for token ID {2}, got {receiver_balance.get('amount')}"
