from os import environ
from urllib.parse import urlparse
import requests
import logging
import json
import coil_wallet.wallet as Wallet
from coil_wallet.util import hex_to_str, str_to_hex
from coil_wallet.outputs import Report, Notice, Voucher
from coil_wallet.ether_processor import EtherProcessor
from coil_wallet.erc20_processor import Erc20Processor
from coil_wallet.erc721_processor import Erc721Processor
from coil_wallet.erc1155_processor import Erc1155Processor


logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

rollup_server = "http://localhost:5004"
if "ROLLUP_HTTP_SERVER_URL" in environ:
    rollup_server = environ["ROLLUP_HTTP_SERVER_URL"]
logger.info(f"HTTP rollup_server url is {rollup_server}")

ether_portal_address = "0xfa2292f6D85ea4e629B156A4f99219e30D12EE17"
erc20_portal_address = "0xB0e28881FF7ee9CD5B1229d570540d74bce23D39"
erc721_portal_address = "0x874b3245ead7474Cb9f3b83cD1446dC522f6bd36"
erc1155_portal_address = "0x2f0D587DD6EcF67d25C558f2e9c3839c579e5e38"
erc1155_batch_portal_address = "0x4a218D331C0933d7E3EB496ac901669f28D94981"

wallet = Wallet
ac = wallet.accs()
ep = EtherProcessor(ac)
e20p = Erc20Processor(ac)
e721p = Erc721Processor(ac)
e1155p = Erc1155Processor(ac)


def decode_json(b):
    s = bytes.fromhex(b[2:]).decode("utf-8")
    d = json.loads(s)
    return d

def handle_advance(data):
    logger.info(f"Received advance request data {data}")
    
    msg_sender = data["metadata"]["msg_sender"].lower()
    payload = data["payload"]
    rollup_address = data["metadata"]["app_contract"].lower()

    response = None

    try:
        # Determine the type of deposit based on the message sender
        notice = handle_deposit(msg_sender, payload)
        if notice:
            response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
            logger.info(f"Received notice status {response.status_code} body {response.content}")
            return "accept"
        
        # Process other routes like transfers and withdrawals
        req_json = decode_json(payload)
        route = req_json.get("route")
        args = req_json.get("args", {})

        """Handle transfer and withdrawal routes."""
        converted_value = lambda value: int(value) if isinstance(value, str) and value.isdigit() else value

        if route == "ether_transfer":
            response = ep.transfer(msg_sender, args["to"].lower(), converted_value(args["amount"])).create()
        elif route == "ether_withdraw":
            response = ep.withdraw(rollup_address.lower(), msg_sender, converted_value(args["amount"])).create()

        elif route == "erc20_transfer":
            response = e20p.transfer(msg_sender, args["to"].lower(), args["erc20"].lower(), converted_value(args["amount"])).create()
        elif route == "erc20_withdraw":
            response = e20p.withdraw(rollup_address, msg_sender, args["erc20"].lower(), converted_value(args["amount"])).create()

        elif route == "erc721_transfer":
            response = e721p.transfer(msg_sender, args["to"].lower(), args["erc721"].lower(), args["token_id"]).create()
        elif route == "erc721_withdraw":
            response = e721p.withdraw(rollup_address, msg_sender, args["erc721"].lower(), args["token_id"]).create()
            
        elif route == "erc1155_transfer":
            response = e1155p.transfer(args["from"].lower(), args["to"].lower(), args["erc1155"].lower(), args["token_id"], converted_value(args["amount"])).create()
        elif route == "erc1155_withdraw":
            response = e1155p.withdraw(rollup_address, msg_sender, args["erc1155"].lower(), args["token_id"], converted_value(args["amount"])).create()
            
        elif route == "erc1155_batch_transfer":
            token_ids = args["token_ids"]
            amounts = [converted_value(amount) for amount in args["amounts"]]
            response = e1155p.batch_transfer(msg_sender, args["to"].lower(), args["erc1155"].lower(), token_ids, amounts).create()
        elif route == "erc1155_batch_withdraw":
            token_ids = args["token_ids"]
            amounts = [converted_value(amount) for amount in args["amounts"]]
            response = e1155p.batch_withdraw(rollup_address, msg_sender, args["erc1155"].lower(), token_ids, amounts).create()
            
        if response:
            logger.info(f"Received notice/voucher status {response.status_code} body {response.content}")

        return "accept"

    except Exception as error:
        handle_error(payload, error)
        return "reject"

def handle_deposit(msg_sender, payload):
    """Process deposit actions based on the sender address."""
    if msg_sender == ether_portal_address.lower():
        return ep.deposit(payload)
    elif msg_sender == erc20_portal_address.lower():
        return e20p.deposit(payload)
    elif msg_sender == erc721_portal_address.lower():
        return e721p.deposit(payload)
    elif msg_sender == erc1155_portal_address.lower():
        return e1155p.deposit(payload)
    elif msg_sender == erc1155_batch_portal_address.lower():
        return e1155p.batch_deposit(payload)
    return None

def handle_error(payload, error):
    """Handle errors in processing."""
    error_msg = f"Failed to process command '{payload}'. {error}"
    Report.from_string(error_msg).create()
    if response:
        logger.info(f"Received report status {response.status_code} body {response.content}")
    logger.info(error_msg, exc_info=True)

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
                wallet.balance_get(account).erc721_get(token_address.lower())
                amount = 1 if token_id in wallet.balance_get(account).erc721_get(token_address.lower()) else 0
            elif token_type == "erc1155":
                token_address, token_id = info[2], int(info[3])
                amount = wallet.balance_get(account).erc1155_get(token_address.lower(), token_id)

            Report.from_json({"token_id": token_id, "amount": amount, "token_type": token_type}).create()
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