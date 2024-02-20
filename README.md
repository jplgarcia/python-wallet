# Python-Wallet

This is a python based Wallet implementation for Cartesi Dapps to handle different types of Assets. Through this wallet a developer can implement functionalities of asset handling inside their dApp, that include depositing asset in the dApp, transfering and withdrawing.

For a full example check the file: https://github.com/jplgarcia/python-wallet/blob/main/dapp.py

## Methods

```
Wallet {
      balance_get,
      _ether_deposit,
      _erc20_deposit,
      _erc721_deposit,
      ether_withdraw,
      ether_transfer,
      erc20_withdraw,
      erc20_transfer,
      erc721_withdraw,
      erc721_transfer
    }
```

## Installing

Install lib through pip
https://pypi.org/project/cartesi-wallet/

```
pip install cartesi-wallet
```

For this lib to run on docker you will need to compile some source code. For that include on your dockerfile `build-essential` in the apt-get install. Like this:

```
apt-get install -y --no-install-recommends build-essential=12.9ubuntu3 busybox-static=1:1.30.1-7ubuntu3 ca-certificates=20230311ubuntu0.22.04.1 curl=7.81.0-1ubuntu1.15
```

To use the Cartesi Wallet module in your project, first, import the module as follows:

```python
import cartesi_wallet.wallet as Wallet
from cartesi_wallet.util import hex_to_str, str_to_hex
import json
```

## Initialization

Create an instance of the Wallet by initializing it with an empty `Map` object:

```python
wallet = Wallet
rollup_address = ""
```

## Checking Balance

To retrieve the balance information from the wallet, use the `balance_get` method. This method should be called within the `inspect` function:

```python
balance = wallet.balance_get(account)
```

The returned `balance` object includes several methods to access specific balance information:

- `ether_get(self) -> int `: Returns the Ether balance as a `int`.
- `erc20_get(self, erc20: str) -> int`: Returns the balance of a ERC20 token as int.
- `erc721_get(self, erc721: str) -> set[int]`: Returns a Set of indexes of the ERC721 tokens owned by the user.

## Asset Handling Methods

For operations such as deposits, transfers, and withdrawals, use the method inside the handle_advance function.

### Deposits

To process a deposit, ensure the sender is the designated portals smart contract (e.g., the default ERC20Portal smart contract from sunodo or nonodo when running locally). You might need to adjust the smart contract address based on your deployment or dynamically retrieve it from a resource file:

```python
msg_sender = data["metadata"]["msg_sender"]
payload = data["payload"]
if msg_sender.lower() == "0x9C21AEb2093C32DDbC53eEF24B873BDCd1aDa1DB".lower():
    notice = wallet.erc20_deposit_process(payload)
    response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
return "accept"
```

### Transfers and Withdrawals

The payload format for transfers and withdrawals may vary with every application. Below is an example payload for the implementations that follow:

```python
# Example payload for "transfer" method
{
    "method": "erc20_transfer",
    "from": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "to": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "erc20": "0xae7f61eCf06C65405560166b259C54031428A9C4",
    "amount": 5000000000000000000
}

# Example payload for "withdraw" method
{
    "method": "erc20_withdraw",
    "from": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "erc20": "0xae7f61eCf06C65405560166b259C54031428A9C4",
    "amount": 3000000000000000000
}
```

Parse the input and process the requested operation accordingly.
Note: the following examples to not check the sender to perform this operations. In such cases is highly recommended to perform a check such as ` msg_sender == req_json["from"] ` so only that individual can perform operations from inside their wallet.

```python
msg_sender = data["metadata"]["msg_sender"]
payload = data["payload"]

try:
    req_json = decode_json(payload)

    if req_json["method"] == "erc20_transfer":
        notice = wallet.erc20_transfer(req_json["from"].lower(), req_json["to"].lower(), req_json["erc20"].lower(), req_json["amount"])
        response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})

    if req_json["method"] == "erc20_withdraw":
        voucher = wallet.erc20_withdraw(req_json["from"].lower(), req_json["erc20"].lower(), req_json["amount"])
        response = requests.post(rollup_server + "/voucher", json={"payload": voucher.payload, "destination": voucher.destination})
    
    return "accept" 

except Exception as error:
    error_msg = f"Failed to process command '{payload}'. {error}"
    response = requests.post(rollup_server + "/report", json={"payload": encode(error_msg)})
    logger.debug(error_msg, exc_info=True)
    return "reject"
```

### Other Tokens

For other token types (e.g., Ether, ERC721), the method signatures are similar, and the logic for deposits, transfers, and withdrawals follows the same pattern as described above.
Here are the functions:

```python
wallet.balance_get(account):

wallet.ether_deposit_process(payload: str):
wallet.ether_withdraw(rollup_address, account, amount):
wallet.erc20_transfer(account, to, erc20, amount):

wallet.erc20_deposit_process(payload:str):
wallet.erc20_withdraw(account, erc20, amount):
wallet.erc20_transfer(account, to, erc20, amount):

wallet.erc721_deposit_process(payload:str):
wallet.erc721_withdraw(rollup_address, sender, erc721, token_id):
wallet.erc721_transfer(account, to, erc721, token_id):
```

Notice that the withdraw operations for both ether and 721 need a argument called `rollup_address` This argument should be set in the dApp. A good way to do it is dinamically with the dApp running through an advance call as well. In the following example the address used is for a contract from the cartesi rollups called "DAppRelay".

```python
if msg_sender.lower() == "0xF5DE34d6BbC0446E2a45719E718efEbaaE179daE".lower():
    global rollup_address
    logger.info(f"Received advance from dapp relay")
    rollup_address = payload
    response = requests.post(rollup_server + "/notice", json={"payload": str_to_hex(f"Set rollup_address {rollup_address}")})
    return "accept"
```

## Snipets
Here are some snipets for you to use:

### Setup
```python
rollup_server = "http://localhost:8080/rollup"#environ["ROLLUP_HTTP_SERVER_URL"]
rollup_server = environ["ROLLUP_HTTP_SERVER_URL"]
logger.info(f"HTTP rollup_server url is {rollup_server}")

# The following addresses are all the one you get when running locally
# Need to be changed for deploy.
dapp_relay_address = "0xF5DE34d6BbC0446E2a45719E718efEbaaE179daE"
ether_portal_address = "0xFfdbe43d4c855BF7e0f105c400A50857f53AB044"
erc20_portal_address = "0x9C21AEb2093C32DDbC53eEF24B873BDCd1aDa1DB"
erc721_portal_address = "0x237F8DD094C0e47f4236f12b4Fa01d6Dae89fb87"

wallet = Wallet
rollup_address = ""
```

### Ether operations
```
{
    "method": "ether_transfer",
    "from": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "to": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "amount": 99000000000000000000
}

{
    "method": "ether_withdraw",
    "from": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "amount": 3000000000000000000
}
```
```python
def handle_advance(data):
    logger.info(f"Received advance request data {data}")
    msg_sender = data["metadata"]["msg_sender"]
    payload = data["payload"]
    print(payload)
  
    # Set Relay 
    if msg_sender.lower() == dapp_relay_address.lower():
        global rollup_address
        logger.info(f"Received advance from dapp relay")
        rollup_address = payload
        response = requests.post(rollup_server + "/notice", json={"payload": str_to_hex(f"Set rollup_address {rollup_address}")})
        return "accept"

    # Deposit
    try:
        notice = None
        if msg_sender.lower() == ether_portal_address.lower():
            notice = wallet.ether_deposit_process(payload)
            response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
        if notice:
            logger.info(f"Received notice status {response.status_code} body {response.content}")
            return "accept"
    except Exception as error:
        error_msg = f"Failed to process deposit '{payload}'. {error}"
        logger.debug(error_msg, exc_info=True)
        return "reject"

    # Transfer and Withdraw
    try:
        req_json = decode_json(payload)
        if req_json["method"] == "ether_transfer":
            notice = wallet.ether_transfer(req_json["from"].lower(), req_json["to"].lower(), req_json["amount"])
            response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
        if req_json["method"] == "ether_withdraw":
            voucher = wallet.ether_withdraw(rollup_address, req_json["from"].lower(), req_json["amount"])
            response = requests.post(rollup_server + "/voucher", json={"payload": voucher.payload, "destination": voucher.destination})
        return "accept" 
    except Exception as error:
        error_msg = f"Failed to process command '{payload}'. {error}"
        response = requests.post(rollup_server + "/report", json={"payload": encode(error_msg)})
        logger.debug(error_msg, exc_info=True)
        return "reject"
```

### ERC20 Operations
```
{
    "method": "erc20_transfer",
    "from" : "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "to": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "erc20": "0xae7f61eCf06C65405560166b259C54031428A9C4",
    "amount": 5000000000000000000
}


{
    "method": "erc20_withdraw",
    "from" : "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "erc20": "0xae7f61eCf06C65405560166b259C54031428A9C4",
    "amount": 3000000000000000000
}
```

```python
def handle_advance(data):
    logger.info(f"Received advance request data {data}")
    msg_sender = data["metadata"]["msg_sender"]
    payload = data["payload"]
    
    # Deposit      
    try:
        notice = None
        if msg_sender.lower() == erc20_portal_address.lower():
            notice = wallet.erc20_deposit_process(payload)
            response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
        if notice:
            logger.info(f"Received notice status {response.status_code} body {response.content}")
            return "accept"
    except Exception as error:
        error_msg = f"Failed to process deposit '{payload}'. {error}"
        logger.debug(error_msg, exc_info=True)
        return "reject"

    # Transfer and Withdraw    
    try:
        req_json = decode_json(payload)
        if req_json["method"] == "erc20_transfer":
            notice = wallet.erc20_transfer(req_json["from"].lower(), req_json["to"].lower(), req_json["erc20"].lower(), req_json["amount"])
            response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})

        if req_json["method"] == "erc20_withdraw":
            voucher = wallet.erc20_withdraw(req_json["from"].lower(), req_json["erc20"].lower(), req_json["amount"])
            response = requests.post(rollup_server + "/voucher", json={"payload": voucher.payload, "destination": voucher.destination})
        return "accept" 
    except Exception as error:
        error_msg = f"Failed to process command '{payload}'. {error}"
        response = requests.post(rollup_server + "/report", json={"payload": encode(error_msg)})
        logger.debug(error_msg, exc_info=True)
        return "reject"
```

### ERC721 Operations
```
{
    "method": "erc721_transfer",
    "from": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "to": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
	"erc721": "0xae7f61eCf06C65405560166b259C54031428A9C4",
    "token_id": 0
}

{
    "method": "erc721_withdraw",
    "from": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
	"erc721": "0xae7f61eCf06C65405560166b259C54031428A9C4",
    "token_id": 1
}
```
```python
def handle_advance(data):
    logger.info(f"Received advance request data {data}")
    msg_sender = data["metadata"]["msg_sender"]
    payload = data["payload"]
    
    # Set Relay
    if msg_sender.lower() == dapp_relay_address.lower():
        global rollup_address
        logger.info(f"Received advance from dapp relay")
        rollup_address = payload
        response = requests.post(rollup_server + "/notice", json={"payload": str_to_hex(f"Set rollup_address {rollup_address}")})
        return "accept"

    # Deposit  
    try:
        notice = None
        if msg_sender.lower() == erc721_portal_address.lower():
            notice = wallet.erc721_deposit_process(payload)
            response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
        if notice:
            logger.info(f"Received notice status {response.status_code} body {response.content}")
            return "accept"
    except Exception as error:
        error_msg = f"Failed to process deposit '{payload}'. {error}"
        logger.debug(error_msg, exc_info=True)
        return "reject"
    
    # Transfer and Withdraw
    try:
        req_json = decode_json(payload)
        if req_json["method"] == "erc721_transfer":
            notice = wallet.erc721_transfer(req_json["from"].lower(), req_json["to"].lower(), req_json["erc721"].lower(), req_json["token_id"])
            response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
        if req_json["method"] == "erc721_withdraw":
            voucher = wallet.erc721_withdraw(rollup_address, req_json["from"].lower(), req_json["erc721"].lower(), req_json["token_id"])
            response = requests.post(rollup_server + "/voucher", json={"payload": voucher.payload, "destination": voucher.destination})
        return "accept" 
    except Exception as error:
        error_msg = f"Failed to process command '{payload}'. {error}"
        response = requests.post(rollup_server + "/report", json={"payload": encode(error_msg)})
        logger.debug(error_msg, exc_info=True)
        return "reject"
```

### Generalist handle inspect
```python
def handle_inspect(data):
    logger.info(f"Received inspect request data {data}")
    try:
        url = urlparse(hex_to_str(data["payload"]))
        if url.path.startswith("balance/"):
            info = url.path.replace("balance/", "").split("/")
            token_type, account = info[0].lower(), info[1].lower()
            token_address, token_id, amount = "", 0, 0

            if (token_type == "ether"):
                amount = wallet.balance_get(account).ether_get()
            elif (token_type == "erc20"):
                token_address = info[2]
                amount = wallet.balance_get(account).erc20_get(token_address.lower())
            elif (token_type == "erc721"):
                token_address, token_id = info[2], info[3]
                amount = 1 if token_id in wallet.balance_get(account).erc721_get(token_address.lower()) else 0
            
            report = {"payload": encode({"token_id": token_id, "amount": amount, "token_type": token_type})}
            response = requests.post(rollup_server + "/report", json=report)
            logger.info(f"Received report status {response.status_code} body {response.content}")
        return "accept"
    except Exception as error:
        error_msg = f"Failed to process inspect request. {error}"
        logger.debug(error_msg, exc_info=True)
        return "reject"
```

Note, routes for this Inspects are as follows:
```
ether:
balance/ether/{wallet}
balance/ether/0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266

erc20:
balance/ether/{wallet}/{token_address}
balance/erc20/0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266/0xae7f61eCf06C65405560166b259C54031428A9C4

erc721:
balance/ether/{wallet}/{token_addres}/{token_id}
balance/erc721/0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266/0xae7f61eCf06C65405560166b259C54031428A9C4/0
```

