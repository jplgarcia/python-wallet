import time
import json
import requests
from conftest import send_transaction, check_balance

ROLLUP_SERVER = "http://localhost:8080"
SLEEP_TIME = 5


def test_deposit_erc721(web3_instance, accounts, portals, dapp_addresses, tokens):
    """
    Test depositing an ERC721 token into the dApp.
    """
    erc721_address = tokens["erc721"]
    token_id = 0

    # Approve the ERC721 portal to transfer the token
    approve_data = web3_instance.to_hex(web3_instance.keccak(text="approve(address,uint256)")[:4])
    encoded_data = web3_instance.codec.encode(["address", "uint256"], [portals["erc721"], token_id])
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_1"],
        accounts["private_key_1"],
        erc721_address,
        approve_data + encoded_data.hex()
    )
    assert tx_hash, "ERC721 token approval failed"
    time.sleep(SLEEP_TIME)

    # Deposit ERC721 token
    deposit_data = web3_instance.to_hex(
        web3_instance.keccak(text="depositERC721Token(address,address,uint256,bytes,bytes)")[:4]
    )
    encoded_data = web3_instance.codec.encode(
        ["address", "address", "uint256", "bytes", "bytes"],
        [erc721_address, dapp_addresses["dapp_address"], token_id, b"", b""],
    )
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_1"],
        accounts["private_key_1"],
        portals["erc721"],
        deposit_data + encoded_data.hex()
    )
    assert tx_hash, "ERC721 token deposit failed"
    time.sleep(SLEEP_TIME)

    # Verify balance after deposit
    balance = check_balance(
        "erc721", accounts["account_1"], dapp_addresses["dapp_address"], token_address=erc721_address, token_id=token_id
    )
    assert balance.get("amount") == 1, f"Expected 1, got {balance.get('amount')}"


def test_transfer_erc721(web3_instance, accounts, dapp_addresses, tokens):
    """
    Test transferring an ERC721 token from account_1 to account_2 via the dApp.
    """
    erc721_address = tokens["erc721"]
    token_id = 0

    transfer_data = {
        "route": "erc721_transfer",
        "args": {
            "from": accounts["account_1"],
            "to": accounts["account_2"],
            "erc721": erc721_address,
            "token_id": token_id,
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
    assert tx_hash, "ERC721 token transfer failed"
    time.sleep(SLEEP_TIME)

    # Verify balances after transfer
    sender_balance = check_balance(
        "erc721", accounts["account_1"], dapp_addresses["dapp_address"], token_address=erc721_address, token_id=token_id
    )
    receiver_balance = check_balance(
        "erc721", accounts["account_2"], dapp_addresses["dapp_address"], token_address=erc721_address, token_id=token_id
    )
    assert sender_balance.get("amount") == 0, f"Expected 0, got {sender_balance.get('amount')}"
    assert receiver_balance.get("amount") == 1, f"Expected 1, got {receiver_balance.get('amount')}"


def test_withdraw_erc721(web3_instance, accounts, dapp_addresses, tokens):
    """
    Test withdrawing an ERC721 token from the dApp to account_2.
    """
    erc721_address = tokens["erc721"]
    token_id = 0

    withdraw_data = {
        "route": "erc721_withdraw",
        "args": {"from": accounts["account_2"], "erc721": erc721_address, "token_id": token_id},
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
    assert tx_hash, "ERC721 token withdrawal failed"
    time.sleep(SLEEP_TIME)

    # Verify balance after withdrawal
    receiver_balance = check_balance(
        "erc721", accounts["account_2"], dapp_addresses["dapp_address"], token_address=erc721_address, token_id=token_id
    )
    assert receiver_balance.get("amount") == 0, f"Expected 0, got {receiver_balance.get('amount')}"
