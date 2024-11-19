import time
from conftest import send_transaction
import json

SLEEP_TIME = 5

def test_deposit_erc1155_batch(web3_instance, accounts, portals, dapp_addresses, tokens, deploy_erc20, deploy_erc721, deploy_erc1155):
    """
    Test depositing multiple ERC1155 tokens into the dApp in a batch.
    """
    token_ids = [1, 2]
    values = [3, 4]

    # Approve the ERC1155 portal to transfer the tokens
    approve_data = web3_instance.to_hex(web3_instance.keccak(text="setApprovalForAll(address,bool)")[:4])
    encoded_data = web3_instance.codec.encode(['address', 'bool'], [portals["erc1155_batch"], True])
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_1"],
        accounts["private_key_1"],
        tokens["erc1155"],
        approve_data + encoded_data.hex()
    )
    assert tx_hash, "ERC1155 batch token approval failed"
    time.sleep(SLEEP_TIME)

    # Deposit the ERC1155 tokens in a batch
    deposit_data = web3_instance.to_hex(web3_instance.keccak(text="depositBatchERC1155Token(address,address,uint256[],uint256[],bytes,bytes)")[:4])
    encoded_data = web3_instance.codec.encode(
        ['address', 'address', 'uint256[]', 'uint256[]', 'bytes', 'bytes'],
        [tokens["erc1155"], dapp_addresses["dapp_address"], token_ids, values, b'', b'']
    )
    tx_hash = send_transaction(
        web3_instance,
        accounts["account_1"],
        accounts["private_key_1"],
        portals["erc1155_batch"],
        deposit_data + encoded_data.hex()
    )
    assert tx_hash, f"ERC1155 batch token deposit failed for token IDs {token_ids} and values {values}"
    time.sleep(SLEEP_TIME)


def test_transfer_erc1155_batch(web3_instance, accounts, dapp_addresses, tokens):
    """
    Test transferring multiple ERC1155 tokens from account_1 to account_2 via the dApp in a batch.
    """
    token_ids = [1, 2]
    values = [2, 3]
    transfer_data = {
        "route": "erc1155_batch_transfer",
        "args": {
            "from": accounts["account_1"],
            "to": accounts["account_2"],
            "erc1155": tokens["erc1155"],
            "token_ids": token_ids,
            "amounts": values
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
    assert tx_hash, f"ERC1155 batch token transfer failed for token IDs {token_ids} and values {values}"
    time.sleep(SLEEP_TIME)


def test_withdraw_erc1155_batch(web3_instance, accounts, dapp_addresses, tokens):
    """
    Test withdrawing multiple ERC1155 tokens from the dApp to account_2 in a batch.
    """
    token_ids = [1, 2]
    values = [1, 2]
    withdraw_data = {
        "route": "erc1155_batch_withdraw",
        "args": {
            "from": accounts["account_2"],
            "erc1155": tokens["erc1155"],
            "token_ids": token_ids,
            "amounts": values
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
    assert tx_hash, f"ERC1155 batch token withdrawal failed for token IDs {token_ids} and values {values}"
    time.sleep(SLEEP_TIME)
