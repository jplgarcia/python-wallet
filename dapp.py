from os import environ
from urllib.parse import urlparse
import requests
import logging
import json
import coil_wallet.wallet as Wallet
from coil_wallet.util import hex_to_str, str_to_hex

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

rollup_server = "http://localhost:5004"
if "ROLLUP_HTTP_SERVER_URL" in environ:
    rollup_server = environ["ROLLUP_HTTP_SERVER_URL"]
logger.info(f"HTTP rollup_server url is {rollup_server}")

dapp_relay_address = "0xF5DE34d6BbC0446E2a45719E718efEbaaE179daE" #open(f'./deployments/{network}/ERC20Portal.json')
ether_portal_address = "0xFfdbe43d4c855BF7e0f105c400A50857f53AB044" #open(f'./deployments/{network}/EtherPortal.json')
erc20_portal_address = "0x9C21AEb2093C32DDbC53eEF24B873BDCd1aDa1DB" #open(f'./deployments/{network}/ERC20Portal.json')
erc721_portal_address = "0x237F8DD094C0e47f4236f12b4Fa01d6Dae89fb87" #open(f'./deployments/{network}/ERC721Portal.json')
erc1155_portal_address = "0x7CFB0193Ca87eB6e48056885E026552c3A941FC4"
erc1155_batch_portal_address = "0xedB53860A6B52bbb7561Ad596416ee9965B055Aa"


wallet = Wallet
rollup_address = ""

def encode(d):
    return "0x" + json.dumps(d).encode("utf-8").hex()

def decode_json(b):
    s = bytes.fromhex(b[2:]).decode("utf-8")
    d = json.loads(s)
    return d

def handle_advance(data):
    logger.info(f"Received advance request data {data}")
    
    msg_sender = data["metadata"]["msg_sender"].lower()
    payload = data["payload"]
    global rollup_address

    try:
        # Check if the request is from the dApp relay
        if msg_sender == dapp_relay_address.lower():
            logger.info("Received advance from dApp relay")
            rollup_address = payload
            response = requests.post(rollup_server + "/notice", json={"payload": str_to_hex(f"Set rollup_address {rollup_address}")})
            return "accept"

        # Determine the type of deposit based on the message sender
        notice = handle_deposit(msg_sender, payload)

        if notice:
            response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
            logger.info(f"Received notice status {response.status_code} body {response.content}")
            return "accept"
        else:
            # Process other routes like transfers and withdrawals
            logger.info("##### will req")
            logger.info(payload)
            req_json = decode_json(payload)
            logger.info(req_json)
            route = req_json.get("route")
            args = req_json.get("args", {})
            notice, voucher = handle_transfer_withdraw(route, args)

            if notice:
                logger.info(f"Received notice status {response.status_code} body {response.content}")
            elif voucher:
                logger.info(f"Received voucher status {response.status_code} body {response.content}")

            return "accept" if (notice or voucher) else "reject"

    except Exception as error:
        handle_error(payload, error)
        return "reject"

def handle_deposit(msg_sender, payload):
    """Process deposit actions based on the sender address."""
    if msg_sender == ether_portal_address.lower():
        return wallet.ether_deposit_process(payload)
    elif msg_sender == erc20_portal_address.lower():
        return wallet.erc20_deposit_process(payload)
    elif msg_sender == erc721_portal_address.lower():
        return wallet.erc721_deposit_process(payload)
    elif msg_sender == erc1155_portal_address.lower():
        return wallet.erc1155_single_deposit_process(payload)
    elif msg_sender == erc1155_batch_portal_address.lower():
        return wallet.erc1155_batch_deposit_process(payload)
    return None

def handle_transfer_withdraw(route, args):
    """Handle transfer and withdrawal routes."""
    notice, voucher, response = None, None, None
    converted_value = lambda value: int(value) if isinstance(value, str) and value.isdigit() else value

    if route == "ether_transfer":
        notice = wallet.ether_transfer(args["from"].lower(), args["to"].lower(), converted_value(args["amount"]))
        response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
    elif route == "ether_withdraw":
        voucher = wallet.ether_withdraw(rollup_address, args["from"].lower(), converted_value(args["amount"]))
        response = requests.post(rollup_server + "/voucher", json={"payload": voucher.payload, "destination": voucher.destination})

    elif route == "erc20_transfer":
        notice = wallet.erc20_transfer(args["from"].lower(), args["to"].lower(), args["erc20"].lower(), converted_value(args["amount"]))
        response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
    elif route == "erc20_withdraw":
        voucher = wallet.erc20_withdraw(args["from"].lower(), args["erc20"].lower(), converted_value(args["amount"]))
        response = requests.post(rollup_server + "/voucher", json={"payload": voucher.payload, "destination": voucher.destination})

    elif route == "erc721_transfer":
        notice = wallet.erc721_transfer(args["from"].lower(), args["to"].lower(), args["erc721"].lower(), args["token_id"])
        response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
    elif route == "erc721_withdraw":
        voucher = wallet.erc721_withdraw(rollup_address, args["from"].lower(), args["erc721"].lower(), args["token_id"])
        response = requests.post(rollup_server + "/voucher", json={"payload": voucher.payload, "destination": voucher.destination})

    elif route == "erc1155_transfer":
        notice = wallet.erc1155_transfer(args["from"].lower(), args["to"].lower(), args["erc1155"].lower(), args["token_id"], converted_value(args["amount"]))
        response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
    elif route == "erc1155_withdraw":
        voucher = wallet.erc1155_withdraw(rollup_address, args["from"].lower(), args["erc1155"].lower(), args["token_id"], converted_value(args["amount"]))
        response = requests.post(rollup_server + "/voucher", json={"payload": voucher.payload, "destination": voucher.destination})

    elif route == "erc1155_batch_transfer":
        token_ids = args["token_ids"]
        amounts = [converted_value(amount) for amount in args["amounts"]]
        notice = wallet.erc1155_batch_transfer(args["from"].lower(), args["to"].lower(), args["erc1155"].lower(), token_ids, amounts)
        response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
    elif route == "erc1155_batch_withdraw":
        token_ids = args["token_ids"]
        amounts = [converted_value(amount) for amount in args["amounts"]]
        voucher = wallet.erc1155_batch_withdraw(rollup_address, args["from"].lower(), args["erc1155"].lower(), token_ids, amounts)
        response = requests.post(rollup_server + "/voucher", json={"payload": voucher.payload, "destination": voucher.destination})

    if response:
        logger.info(f"Received notice/voucher status {response.status_code} body {response.content}")

    return notice, voucher

def handle_error(payload, error):
    """Handle errors in processing."""
    error_msg = f"Failed to process command '{payload}'. {error}"
    response = requests.post(rollup_server + "/report", json={"payload": encode(error_msg)})
    if response:
        logger.info(f"Received report status {response.status_code} body {response.content}")
    logger.debug(error_msg, exc_info=True)

def handle_inspect(data):
    logger.info(f"Received inspect request data {data}")
    try:
        url = urlparse(hex_to_str(data["payload"]))
        if url.path.startswith("balance/"):
            info = url.path.replace("balance/", "").split("/")
            token_type, account = info[0].lower(), info[1].lower()
            token_address, token_id, amount = "", 0, 0

            if token_type == "ether":
                amount = wallet.balance_get(account).ether_get()
            elif token_type == "erc20":
                token_address = info[2]
                amount = wallet.balance_get(account).erc20_get(token_address.lower())
            elif token_type == "erc721":
                token_address, token_id = info[2], int(info[3])
                logger.info(f"checking balance for {token_id} of {token_address} in wallet {account}")
                wallet.balance_get(account).erc721_get(token_address.lower())
                amount = 1 if token_id in wallet.balance_get(account).erc721_get(token_address.lower()) else 0
            elif token_type == "erc1155":
                token_address, token_id = info[2], int(info[3])
                amount = wallet.balance_get(account).erc1155_get(token_address.lower(), token_id)

            report = {"payload": encode({"token_id": token_id, "amount": amount, "token_type": token_type})}
            response = requests.post(rollup_server + "/report", json=report)
            logger.info(f"Received report status {response.status_code} body {response.content}")
        
        return "accept"
    except Exception as error:
        error_msg = f"Failed to process inspect request. {error}"
        logger.debug(error_msg, exc_info=True)
        return "reject"



handlers = {
    "advance_state": handle_advance,
    "inspect_state": handle_inspect,
}

finish = {"status": "accept"}

while True:
    logger.info("Sending finish")
    response = requests.post(rollup_server + "/finish", json=finish)
    logger.info(f"Received finish status {response.status_code}")
    if response.status_code == 202:
        logger.info("No pending rollup request, trying again")
    else:
        rollup_request = response.json()
        data = rollup_request["data"]
        handler = handlers[rollup_request["request_type"]]
        finish["status"] = handler(rollup_request["data"])