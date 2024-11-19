import time
import json
import requests
from eth_abi import encode
from conftest import send_transaction, check_balance

ROLLUP_SERVER = "http://localhost:8080"
SLEEP_TIME = 5


def test_deposit_erc20(web3_instance, accounts, portals, dapp_addresses, tokens):
    """
    Test depositing ERC20 tokens into the dApp.
    """
    erc20_address = tokens["erc20"]
    value = web3_instance.to_wei(1000, "ether")

    # Approve the ERC20 portal to transfer tokens
    print('will approve')
    approve_data = web3_instance.to_hex(web3_instance.keccak(text="approve(address,uint256)")[:4])
    encoded_data = encode(["address", "uint256"], [portals["erc20"], value])
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_1"],
        accounts["private_key_1"],
        erc20_address,
        approve_data + encoded_data.hex()
    )
    print('did approve')

    assert tx_hash, "ERC20 token approval failed"
    time.sleep(SLEEP_TIME)

    # Deposit ERC20 tokens
    deposit_data = web3_instance.to_hex(
        web3_instance.keccak(text="depositERC20Tokens(address,address,uint256,bytes)")[:4]
    )
    encoded_data = encode(
        ["address", "address", "uint256", "bytes"],
        [erc20_address, dapp_addresses["dapp_address"], value, b""],
    )
    print('will depo')

    tx_hash = send_transaction(
        web3_instance,
        accounts["account_1"],
        accounts["private_key_1"],
        portals["erc20"],
        deposit_data + encoded_data.hex()
    )
    print('did depo')

    assert tx_hash, "ERC20 token deposit failed"
    time.sleep(SLEEP_TIME)

    # Verify balance after deposit
    balance = check_balance("erc20", accounts["account_1"], dapp_addresses["dapp_address"], token_address=erc20_address)
    assert balance.get("amount") == value, f"Expected {value}, got {balance.get('amount')}"


def test_transfer_erc20(web3_instance, accounts, dapp_addresses, tokens):
    """
    Test transferring ERC20 tokens from account_1 to account_2 via the dApp.
    """
    erc20_address = tokens["erc20"]
    value = web3_instance.to_wei(500, "ether")

    transfer_data = {
        "route": "erc20_transfer",
        "args": {
            "from": accounts["account_1"],
            "to": accounts["account_2"],
            "erc20": erc20_address,
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
    assert tx_hash, "ERC20 token transfer failed"
    time.sleep(SLEEP_TIME)

    # Verify balances after transfer
    sender_balance = check_balance(
        "erc20", accounts["account_1"], dapp_addresses["dapp_address"], token_address=erc20_address
    )
    receiver_balance = check_balance(
        "erc20", accounts["account_2"], dapp_addresses["dapp_address"], token_address=erc20_address
    )
    assert sender_balance.get("amount") == web3_instance.to_wei(500, "ether"), (
        f"Expected 500, got {sender_balance.get('amount')}"
    )
    assert receiver_balance.get("amount") == value, (
        f"Expected {value}, got {receiver_balance.get('amount')}"
    )


def test_withdraw_erc20(web3_instance, accounts, dapp_addresses, tokens):
    """
    Test withdrawing ERC20 tokens from the dApp to account_2.
    """
    erc20_address = tokens["erc20"]
    value = web3_instance.to_wei(500, "ether")

    withdraw_data = {
        "route": "erc20_withdraw",
        "args": {"from": accounts["account_2"], "erc20": erc20_address, "amount": value},
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
    assert tx_hash, "ERC20 token withdrawal failed"
    time.sleep(SLEEP_TIME)

    # Verify balance after withdrawal
    receiver_balance = check_balance(
        "erc20", accounts["account_2"], dapp_addresses["dapp_address"], token_address=erc20_address
    )
    assert receiver_balance.get("amount") == 0, (
        f"Expected 0, got {receiver_balance.get('amount')}"
    )
