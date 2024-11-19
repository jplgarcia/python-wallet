import pytest
import json
from web3 import Web3
import requests
import subprocess


# Constants
# w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
ROLLUP_SERVER = "http://localhost:8080"

@pytest.fixture(scope="module")
def web3_instance():
    print("Initializing Web3 instance...")
    return Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

@pytest.fixture(scope="module")
def deploy_erc20():
    """
    Fixture to deploy the ERC20 contract and return its address.
    """
    script_path = "./deploy_erc20.sh"  # Path to your deployment script
    print("deploying erc20...")
    return deploy_contract(script_path)

@pytest.fixture(scope="module")
def deploy_erc721():
    """
    Fixture to deploy the ERC721 contract and return its address.
    """
    script_path = "./deploy_erc721.sh"
    print("deploying erc20...")
    return deploy_contract(script_path)

@pytest.fixture(scope="module")
def deploy_erc1155():
    """
    Fixture to deploy the ERC1155 contract and return its address.
    """
    script_path = "./deploy_erc1155.sh"
    print("deploying erc20...")
    return deploy_contract(script_path)

@pytest.fixture
def accounts():
    print("setting accs...")
    return {
        "account_1": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "private_key_1": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
        "account_2": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "private_key_2": "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
    }

@pytest.fixture
def dapp_addresses():
    print("setting dapp addresses...")
    return {
        "dapp_address": "0x75135d8ADb7180640d29d822D9AD59E83E8695b2",
        "input_box_address": "0x593E5BCf894D6829Dd26D0810DA7F064406aebB6",
    }

@pytest.fixture
def portals():
    print("setting portal addresses...")
    return {
        "ether": "0xfa2292f6D85ea4e629B156A4f99219e30D12EE17",
        "erc20": "0xB0e28881FF7ee9CD5B1229d570540d74bce23D39",
        "erc721": "0x874b3245ead7474Cb9f3b83cD1446dC522f6bd36",
        "erc1155": "0x2f0D587DD6EcF67d25C558f2e9c3839c579e5e38",
        "erc1155_batch": "0x4a218D331C0933d7E3EB496ac901669f28D94981",
    }

@pytest.fixture
def tokens():
    print("setting token addresses...")
    return {
        "erc20": "0x9A676e781A523b5d0C0e43731313A708CB607508",
        "erc721": "0x0B306BF915C4d645ff596e518fAf3F9669b97016",
        "erc1155": "0x959922bE3CAee4b8Cd9a407cc3ac1C251C2007B1",
    }


def send_transaction(w3, from_account, private_key, to, data, value=0):
    print(w3, from_account, private_key, to, data, value)
    tx = {
        'to': to,
        'data': data,
        'value': value,
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei'),
        'nonce': w3.eth.get_transaction_count(from_account),
    }
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_reponse = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(tx_reponse)
    hex_tx = w3.to_hex(tx_reponse)
    return hex_tx

def check_balance(token_type, account, dapp_address, token_address=None, token_id=None):
    """
    Helper function to check the balance of Ether.

    Args:
        token_type (str): The type of token (e.g., 'ether', 'erc20', etc.).
        account (str): The account address to check the balance for.
        dapp_address (str): The address of the dApp.
        token_address (str, optional): The token contract address (not used for Ether).

    Returns:
        dict: Parsed balance data from the rollup server.
    """
    # Construct the path for the inspect call
    path = f"balance/{token_type}/{account}"
    if(token_address): 
        path += f"/{token_address}"

    if(token_id is not None): 
        path += f"/{token_id}"

    # Send the inspect request to the rollup server
    response = requests.get(f"{ROLLUP_SERVER}/inspect/{dapp_address}/{path}")
    assert response.status_code == 200, f"Failed to inspect balance for {token_type}"

    # Parse and return balance data
    response_data = response.json()
    print(response_data)
    return parse_balance_response(response_data)

def parse_balance_response(response_content):
    # Parse the payload nested in 'reports' > 0 > 'payload'
    report = response_content.get("reports", [{}])[0].get("payload", "")
    if report:
        # Decode the payload if it's encoded in hex
        decoded_report = bytes.fromhex(report[2:]).decode('utf-8')  # Remove '0x' and decode
        return json.loads(decoded_report)
    return None

def deploy_contract(script_path):
    """
    Deploy a contract using a deployment script and return the deployed contract address.

    Args:
        script_path (str): Path to the deployment script.

    Returns:
        str: The deployed contract address.
    """
    result = subprocess.run(
        [script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Deployment script failed: {result.stderr}")
    # Extract the contract address from the script's output
    address = result.stdout.strip()
    if not address.startswith("0x"):
        raise ValueError(f"Invalid contract address returned: {address}")
    return address