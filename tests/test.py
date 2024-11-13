import pytest
import requests
import json
from urllib.parse import urlencode
from web3 import Web3
from eth_account import Account
from eth_abi import encode
import logging
import time
import subprocess


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SLEEP_TIME = 5

rollup_server = "http://localhost:8080"

# Setup Web3 connection to local node
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Addresses and Private Keys
account_1 = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"  # Wallet for deposits
private_key_1 = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

account_2 = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"  # Wallet for transfers/withdrawals
private_key_2 = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"

# Dapp and Portal Addresses
dapp_address = "0xab7528bb862fb57e8a2bcd567a2e929a0be56a5e"
input_box_address = "0x59b22D57D4f067708AB0c00552767405926dc768"

# Portals
ether_portal_address = "0xFfdbe43d4c855BF7e0f105c400A50857f53AB044"
erc20_portal_address = "0x9C21AEb2093C32DDbC53eEF24B873BDCd1aDa1DB"
erc721_portal_address = "0x237F8DD094C0e47f4236f12b4Fa01d6Dae89fb87"
erc1155_portal_address = "0x7CFB0193Ca87eB6e48056885E026552c3A941FC4"
erc1155_batch_portal_address = "0xedB53860A6B52bbb7561Ad596416ee9965B055Aa"

# Tokens
erc20_token_address = "0x92C6bcA388E99d6B304f1Af3c3Cd749Ff0b591e2"
erc721_token_address = "0x36C02dA8a0983159322a80FFE9F24b1acfF8B570"
erc1155_token_address = "0x809d550fca64d94Bd9F66E60752A544199cfAC3D"

script1 = "./deploy_erc721.sh"
script2 = "./deploy+erc1155.sh"

# Helper function to send transactions
def send_transaction(to, data, value=0):
    tx = {
        'to': to,
        'data': data,
        'value': w3.to_wei(value, 'ether'),
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei'),
        'nonce': w3.eth.get_transaction_count(account_1),
    }
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key_1)
    return w3.to_hex(w3.eth.send_raw_transaction(signed_tx.raw_transaction))

def send_transaction_from_account_2(to, data, value=0):
    tx = {
        'to': to,
        'data': data,
        'value': w3.to_wei(value, 'ether'),
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei'),
        'nonce': w3.eth.get_transaction_count(account_2),
    }
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key_2)
    return w3.to_hex(w3.eth.send_raw_transaction(signed_tx.raw_transaction))

def parse_balance_response(response_content):
    # The payload is nested in 'reports' > 0 > 'payload'
    report = response_content.get("reports", [{}])[0].get("payload", "")
    if report:
        # Decode the payload if it's encoded in hex
        decoded_report = bytes.fromhex(report[2:]).decode('utf-8')  # Remove '0x' and decode
        return json.loads(decoded_report)
    return None

# Ordered Test Class
class TestDepositsAndTransfers:

    # def deploy_contracts(self):
    #     # Run the first script
    #     result1 = subprocess.run(["bash", script1], capture_output=True, text=True)
    #     print("Script 1 output:", result1.stdout)
    #     if result1.stderr:
    #         print("Script 1 error:", result1.stderr)
    #     time.sleep(SLEEP_TIME)


    #     # Run the second script
    #     result2 = subprocess.run(["bash", script2], capture_output=True, text=True)
    #     print("Script 2 output:", result2.stdout)
    #     if result2.stderr:
    #         print("Script 2 error:", result2.stderr)

    #     time.sleep(SLEEP_TIME)

    def test_deposit_ether(self):
        value = 1000
        data = Web3.to_hex(Web3.keccak(text="depositEther(address,bytes)")[:4])

        encoded_data = encode(['address', 'bytes'], [dapp_address, b''])
        tx_hash = send_transaction(ether_portal_address, data + encoded_data.hex(), value)

        assert tx_hash, f"Ether deposit failed for {value} ETH."
        time.sleep(SLEEP_TIME)


    def test_deposit_erc20(self):
        value = 1000

        data = Web3.to_hex(Web3.keccak(text="approve(address,uint256)")[:4])
        encoded_data = encode(['address', 'uint256'], [erc20_portal_address, w3.to_wei(value, 'ether')])
        tx_hash = send_transaction(erc20_token_address, data + encoded_data.hex())
        time.sleep(SLEEP_TIME)

        data = Web3.to_hex(Web3.keccak(text="depositERC20Tokens(address,address,uint256,bytes)")[:4])
        encoded_data = encode(['address', 'address', 'uint256', 'bytes'], [erc20_token_address, dapp_address, w3.to_wei(value, 'ether'), b''])
        tx_hash = send_transaction(erc20_portal_address, data + encoded_data.hex())

        assert tx_hash, f"ERC20 deposit failed for {value} tokens."
        time.sleep(SLEEP_TIME)


    # def test_deposit_erc721(self):

    #     data = Web3.to_hex(Web3.keccak(text="approve(address,uint256)")[:4])
    #     encoded_data = encode(['address', 'uint256'], [erc721_portal_address, 0])
    #     tx_hash = send_transaction(erc721_token_address, data + encoded_data.hex())
    #     time.sleep(SLEEP_TIME)

    #     token_id = 0
    #     data = Web3.to_hex(Web3.keccak(text="depositERC721Token(address,address,uint256,bytes,bytes)")[:4])
    #     encoded_data = encode(['address', 'address', 'uint256', 'bytes', 'bytes'], [erc721_token_address, dapp_address, token_id, b'', b''])
    #     tx_hash = send_transaction(erc721_portal_address, data + encoded_data.hex())

    #     assert tx_hash, f"ERC721 deposit failed for token ID {token_id}."
    #     time.sleep(SLEEP_TIME)


    # def test_deposit_erc1155(self):
    #     data = Web3.to_hex(Web3.keccak(text="setApprovalForAll(address,bool)")[:4])
    #     encoded_data = encode(['address', 'bool'], [erc1155_portal_address, True])
    #     tx_hash = send_transaction(erc1155_token_address, data + encoded_data.hex())
        
    #     assert tx_hash, f"ERC1155 allowance failed."
    #     time.sleep(SLEEP_TIME)
    
    #     token_id, value = 1, 2
    #     data = Web3.to_hex(Web3.keccak(text="depositSingleERC1155Token(address,address,uint256,uint256,bytes,bytes)")[:4])
    #     encoded_data = encode(['address', 'address', 'uint256', 'uint256', 'bytes', 'bytes'], [erc1155_token_address, dapp_address, token_id, value, b'', b''])
    #     tx_hash = send_transaction(erc1155_portal_address, data + encoded_data.hex())

    #     assert tx_hash, f"ERC1155 single deposit failed for token ID {token_id}, value {value}."
    #     time.sleep(SLEEP_TIME)


    # def test_deposit_erc1155_batch(self):
    #     data = Web3.to_hex(Web3.keccak(text="setApprovalForAll(address,bool)")[:4])
    #     encoded_data = encode(['address', 'bool'], [erc1155_batch_portal_address, True])
    #     tx_hash = send_transaction(erc1155_token_address, data + encoded_data.hex())

    #     assert tx_hash, f"ERC1155 allowance failed."
    #     time.sleep(SLEEP_TIME)

    #     token_ids, values = [1, 2], [3, 4]
    #     data = Web3.to_hex(Web3.keccak(text="depositBatchERC1155Token(address,address,uint256[],uint256[],bytes,bytes)")[:4])
    #     encoded_data = encode(['address', 'address', 'uint256[]', 'uint256[]', 'bytes', 'bytes'], [erc1155_token_address, dapp_address, token_ids, values, b'', b''])
    #     tx_hash = send_transaction(erc1155_batch_portal_address, data + encoded_data.hex())

    #     assert tx_hash, f"ERC1155 batch deposit failed for token IDs {token_ids}."
    #     time.sleep(SLEEP_TIME)

    # @pytest.mark.parametrize("token_type, account, token_address, token_id, expected_balance", [
    #     ("ether", account_1, None, None, w3.to_wei(1000, 'ether')),
    #     ("erc20", account_1, erc20_token_address.lower(), None, w3.to_wei(1000, 'ether')),
    #     ("erc721", account_1, erc721_token_address, 0, 1),
    #     ("erc1155", account_1, erc1155_token_address, 1, 5),
    #     ("erc1155", account_1, erc1155_token_address, 2, 4),

    # ])
    # def test_inspect_balance(self, token_type, account, token_address, token_id, expected_balance):
    #     # Construct the path
    #     path = f"balance/{token_type}/{account}"
    #     if token_address:
    #         path += f"/{token_address}"
    #     if token_id is not None:
    #         path += f"/{token_id}"

    #     # Send the inspect request to the server
    #     response = requests.get(f"{rollup_server}/inspect/{path}")
    #     assert response.status_code == 200, f"Failed to inspect balance for {token_type}"

    #     # Parse and validate the balance response
    #     response_data = response.json()
    #     balance_data = parse_balance_response(response_data)

    #     assert balance_data is not None, "Failed to retrieve balance data"
    #     assert balance_data.get("amount") == expected_balance, (
    #         f"Expected balance {expected_balance} but got {balance_data.get('amount')}"
    #     )
    #     assert balance_data.get("token_type") == token_type, (
    #         f"Expected token type {token_type} but got {balance_data.get('token_type')}"
    #     )
    #     if token_id is not None:
    #         assert balance_data.get("token_id") == token_id, (
    #             f"Expected token ID {token_id} but got {balance_data.get('token_id')}"
    #         )

    #     print(f"Balance check passed for {token_type}, account {account}")

    def test_transfer(self):
        transfers = [
            ("ether_transfer", {"from": account_1, "to": account_2, "amount": w3.to_wei(1000, 'ether')}),
            ("erc20_transfer", {"from": account_1, "to": account_2, "erc20": erc20_token_address, "amount": w3.to_wei(1000, 'ether')}),
            # ("erc721_transfer", {"from": account_1, "to": account_2, "erc721": erc721_token_address, "token_id": 0}),
            # ("erc1155_transfer", {"from": account_1, "to": account_2, "erc1155": erc1155_token_address, "token_id": 1, "amount": 2}),
            # ("erc1155_batch_transfer", {"from": account_1, "to": account_2, "erc1155": erc1155_token_address, "token_ids": [1, 2], "amounts": [2, 4]}),
        ]
        for route, args in transfers:
            input_data = {
                "route": route,
                "args": args
            }
            encoded_data = Web3.to_hex(Web3.keccak(text="addInput(address,bytes)")[:4])
            encoded_input = encode(['address', 'bytes'], [dapp_address, Web3.to_bytes(text=json.dumps(input_data))])
            tx_hash = send_transaction(input_box_address, encoded_data + encoded_input.hex())
            assert tx_hash, f"Transfer or withdrawal failed for route {route}."
            time.sleep(SLEEP_TIME)


    # @pytest.mark.parametrize("token_type, account, token_address, token_id, expected_balance", [
    #     ("ether", account_2, None, None, w3.to_wei(1000, 'ether')),
    #     ("erc20", account_2, erc20_token_address.lower(), None, w3.to_wei(1000, 'ether')),
    #     ("erc721", account_2, erc721_token_address, 0, 1),
    #     ("erc1155", account_2, erc1155_token_address, 1, 4),
    #     ("erc1155", account_2, erc1155_token_address, 2, 4),

    # ])
    # def test_inspect_balance_account2(self, token_type, account, token_address, token_id, expected_balance):
    #     # Construct the path
    #     path = f"balance/{token_type}/{account}"
    #     if token_address:
    #         path += f"/{token_address}"
    #     if token_id is not None:
    #         path += f"/{token_id}"

    #     # Send the inspect request to the server
    #     response = requests.get(f"{rollup_server}/inspect/{path}")
    #     assert response.status_code == 200, f"Failed to inspect balance for {token_type}"

    #     # Parse and validate the balance response
    #     response_data = response.json()

    #     balance_data = parse_balance_response(response_data)

    #     assert balance_data is not None, "Failed to retrieve balance data"
    #     assert balance_data.get("amount") == expected_balance, (
    #         f"Expected balance {expected_balance} but got {balance_data.get('amount')}"
    #     )
    #     assert balance_data.get("token_type") == token_type, (
    #         f"Expected token type {token_type} but got {balance_data.get('token_type')}"
    #     )
    #     if token_id is not None:
    #         assert balance_data.get("token_id") == token_id, (
    #             f"Expected token ID {token_id} but got {balance_data.get('token_id')}"
    #         )

    #     print(f"Balance check passed for {token_type}, account {account}")

    def test_withdraw_ether(self):
        value = w3.to_wei(500, 'ether')  # Withdrawal amount
        input_data = {
            "route": "ether_withdraw",
            "args": {"from": account_2, "amount": value}
        }
        encoded_data = Web3.to_hex(Web3.keccak(text="addInput(address,bytes)")[:4])
        encoded_input = encode(['address', 'bytes'], [dapp_address, Web3.to_bytes(text=json.dumps(input_data))])
        tx_hash = send_transaction_from_account_2(input_box_address, encoded_data + encoded_input.hex())
        
        assert tx_hash, f"Ether withdrawal failed for {value} ETH."
        time.sleep(SLEEP_TIME)

    def test_withdraw_erc20(self):
        value = w3.to_wei(500, 'ether')  # Withdrawal amount
        input_data = {
            "route": "erc20_withdraw",
            "args": {"from": account_2, "erc20": erc20_token_address, "amount": value}
        }
        encoded_data = Web3.to_hex(Web3.keccak(text="addInput(address,bytes)")[:4])
        encoded_input = encode(['address', 'bytes'], [dapp_address, Web3.to_bytes(text=json.dumps(input_data))])
        tx_hash = send_transaction_from_account_2(input_box_address, encoded_data + encoded_input.hex())
        
        assert tx_hash, f"ERC20 withdrawal failed for {value} tokens."
        time.sleep(SLEEP_TIME)

    # def test_withdraw_erc721(self):
    #     token_id = 0  # Token ID to withdraw
    #     input_data = {
    #         "route": "erc721_withdraw",
    #         "args": {"from": account_2, "erc721": erc721_token_address, "token_id": token_id}
    #     }
    #     encoded_data = Web3.to_hex(Web3.keccak(text="addInput(address,bytes)")[:4])
    #     encoded_input = encode(['address', 'bytes'], [dapp_address, Web3.to_bytes(text=json.dumps(input_data))])
    #     tx_hash = send_transaction_from_account_2(input_box_address, encoded_data + encoded_input.hex())
        
    #     assert tx_hash, f"ERC721 withdrawal failed for token ID {token_id}."
    #     time.sleep(SLEEP_TIME)

    # def test_withdraw_erc1155(self):
    #     token_id, value = 1, 2  # Token ID and amount to withdraw
    #     input_data = {
    #         "route": "erc1155_withdraw",
    #         "args": {"from": account_2, "erc1155": erc1155_token_address, "token_id": token_id, "amount": value}
    #     }
    #     encoded_data = Web3.to_hex(Web3.keccak(text="addInput(address,bytes)")[:4])
    #     encoded_input = encode(['address', 'bytes'], [dapp_address, Web3.to_bytes(text=json.dumps(input_data))])
    #     tx_hash = send_transaction_from_account_2(input_box_address, encoded_data + encoded_input.hex())
        
    #     assert tx_hash, f"ERC1155 withdrawal failed for token ID {token_id}, amount {value}."
    #     time.sleep(SLEEP_TIME)

    # def test_withdraw_erc1155_batch(self):
    #     token_ids, values = [1, 2], [1, 2]  # Token IDs and amounts to withdraw
    #     input_data = {
    #         "route": "erc1155_batch_withdraw",
    #         "args": {"from": account_2, "erc1155": erc1155_token_address, "token_ids": token_ids, "amounts": values}
    #     }
    #     encoded_data = Web3.to_hex(Web3.keccak(text="addInput(address,bytes)")[:4])
    #     encoded_input = encode(['address', 'bytes'], [dapp_address, Web3.to_bytes(text=json.dumps(input_data))])
    #     tx_hash = send_transaction_from_account_2(input_box_address, encoded_data + encoded_input.hex())
        
    #     assert tx_hash, f"ERC1155 batch withdrawal failed for token IDs {token_ids}."
    #     time.sleep(SLEEP_TIME)

    # @pytest.mark.parametrize("token_type, account, token_address, token_id, expected_balance", [
    #     ("ether", account_2, None, None, w3.to_wei(500, 'ether')),
    #     ("erc20", account_2, erc20_token_address.lower(), None, w3.to_wei(500, 'ether')),
    #     ("erc721", account_2, erc721_token_address, 0, 0),
    #     ("erc1155", account_2, erc1155_token_address, 1, 1),
    #     ("erc1155", account_2, erc1155_token_address, 2, 2),

    # ])
    # def test_inspect_balance_account2_again(self, token_type, account, token_address, token_id, expected_balance):
    #     # Construct the path
    #     path = f"balance/{token_type}/{account}"
    #     if token_address:
    #         path += f"/{token_address}"
    #     if token_id is not None:
    #         path += f"/{token_id}"

    #     # Send the inspect request to the server
    #     response = requests.get(f"{rollup_server}/inspect/{path}")
    #     assert response.status_code == 200, f"Failed to inspect balance for {token_type}"

    #     # Parse and validate the balance response
    #     response_data = response.json()

    #     balance_data = parse_balance_response(response_data)

    #     assert balance_data is not None, "Failed to retrieve balance data"
    #     assert balance_data.get("amount") == expected_balance, (
    #         f"Expected balance {expected_balance} but got {balance_data.get('amount')}"
    #     )
    #     assert balance_data.get("token_type") == token_type, (
    #         f"Expected token type {token_type} but got {balance_data.get('token_type')}"
    #     )
    #     if token_id is not None:
    #         assert balance_data.get("token_id") == token_id, (
    #             f"Expected token ID {token_id} but got {balance_data.get('token_id')}"
    #         )

    #     print(f"Balance check passed for {token_type}, account {account}")