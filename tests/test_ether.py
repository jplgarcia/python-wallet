import time
import json
import requests
from eth_abi import encode
from conftest import send_transaction, check_balance

ROLLUP_SERVER = "http://localhost:8080"
SLEEP_TIME = 5



def test_deposit_ether(web3_instance, accounts, portals, dapp_addresses):
    """
    Test depositing Ether into the dApp.
    """
    value = web3_instance.to_wei(1000, 'ether')

    # Deposit Ether
    deposit_data = web3_instance.to_hex(web3_instance.keccak(text="depositEther(address,bytes)")[:4])
    encoded_data = encode(['address', 'bytes'], [dapp_addresses["dapp_address"], b''])
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_1"],
        accounts["private_key_1"],
        portals["ether"],
        deposit_data + encoded_data.hex(),
        value=value
    )
    assert tx_hash, "Ether deposit failed"
    time.sleep(SLEEP_TIME)

    # Verify balance after deposit
    balance = check_balance("ether", accounts["account_1"], dapp_addresses["dapp_address"])
    assert balance.get("amount") == value, f"Expected {value}, got {balance.get('amount')}"


def test_transfer_ether(web3_instance, accounts, dapp_addresses):
    """
    Test transferring Ether from account_1 to account_2 via the dApp.
    """
    value = web3_instance.to_wei(500, 'ether')

    transfer_data = {
        "route": "ether_transfer",
        "args": {
            "from": accounts["account_1"],
            "to": accounts["account_2"],
            "amount": value
        }
    }
    encoded_data = web3_instance.to_hex(web3_instance.keccak(text="addInput(address,bytes)")[:4])
    encoded_input = web3_instance.codec.encode(
        ['address', 'bytes'],
        [dapp_addresses["dapp_address"], web3_instance.to_bytes(text=json.dumps(transfer_data))]
    )
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_1"],
        accounts["private_key_1"],
        dapp_addresses["input_box_address"],
        encoded_data + encoded_input.hex()
    )
    assert tx_hash, "Ether transfer failed"
    time.sleep(SLEEP_TIME)

    # Verify balances after transfer
    sender_balance = check_balance("ether", accounts["account_1"], dapp_addresses["dapp_address"])
    receiver_balance = check_balance("ether", accounts["account_2"], dapp_addresses["dapp_address"])
    assert sender_balance.get("amount") == web3_instance.to_wei(500, 'ether'), (
        f"Expected 500, got {sender_balance.get('amount')}"
    )
    assert receiver_balance.get("amount") == value, f"Expected {value}, got {receiver_balance.get('amount')}"


def test_withdraw_ether(web3_instance, accounts, dapp_addresses):
    """
    Test withdrawing Ether from the dApp to account_2.
    """
    value = web3_instance.to_wei(500, 'ether')

    withdraw_data = {
        "route": "ether_withdraw",
        "args": {
            "from": accounts["account_2"],
            "amount": value
        }
    }
    encoded_data = web3_instance.to_hex(web3_instance.keccak(text="addInput(address,bytes)")[:4])
    encoded_input = web3_instance.codec.encode(
        ['address', 'bytes'],
        [dapp_addresses["dapp_address"], web3_instance.to_bytes(text=json.dumps(withdraw_data))]
    )
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_2"],
        accounts["private_key_2"],
        dapp_addresses["input_box_address"],
        encoded_data + encoded_input.hex()
    )
    assert tx_hash, "Ether withdrawal failed"
    time.sleep(SLEEP_TIME)

    # Verify balance after withdrawal
    receiver_balance = check_balance("ether", accounts["account_2"], dapp_addresses["dapp_address"])
    assert receiver_balance.get("amount") == 0, f"Expected 0, got {receiver_balance.get('amount')}"
