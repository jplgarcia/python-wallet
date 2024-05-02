from os import environ
from urllib.parse import urlparse
import requests
import logging
import json
import cartesi_wallet.wallet as Wallet
from cartesi_wallet.util import hex_to_str, str_to_hex

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
    msg_sender = data["metadata"]["msg_sender"]
    payload = data["payload"]
    print(payload)
  
    if msg_sender.lower() == dapp_relay_address.lower():
        global rollup_address
        logger.info(f"Received advance from dapp relay")
        rollup_address = payload
        response = requests.post(rollup_server + "/notice", json={"payload": str_to_hex(f"Set rollup_address {rollup_address}")})
        return "accept"
        
    try:
        notice = None
        if msg_sender.lower() == ether_portal_address.lower():
            notice = wallet.ether_deposit_process(payload)
            response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
        elif msg_sender.lower() == erc20_portal_address.lower():
            notice = wallet.erc20_deposit_process(payload)
            response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
        elif msg_sender.lower() == erc721_portal_address.lower():
            notice = wallet.erc721_deposit_process(payload)
            response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})
        if notice:
            logger.info(f"Received notice status {response.status_code} body {response.content}")
            return "accept"
    except Exception as error:
        error_msg = f"Failed to process command '{payload}'. {error}"
        response = requests.post(rollup_server + "/report", json={"payload": encode(error_msg)})
        logger.debug(error_msg, exc_info=True)
        return "reject"
        
    try:
        req_json = decode_json(payload)
        print(req_json)
        if req_json["method"] == "ether_transfer":
            converted_value = int(req_json["amount"]) if isinstance(req_json["amount"], str) and req_json["amount"].isdigit() else req_json["amount"]
            notice = wallet.ether_transfer(req_json["from"].lower(), req_json["to"].lower(), converted_value)
            response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})

        if req_json["method"] == "ether_withdraw":
            converted_value = int(req_json["amount"]) if isinstance(req_json["amount"], str) and req_json["amount"].isdigit() else req_json["amount"]
            voucher = wallet.ether_withdraw(rollup_address, req_json["from"].lower(), converted_value)
            response = requests.post(rollup_server + "/voucher", json={"payload": voucher.payload, "destination": voucher.destination})

        if req_json["method"] == "erc20_transfer":
            converted_value = int(req_json["amount"]) if isinstance(req_json["amount"], str) and req_json["amount"].isdigit() else req_json["amount"]
            notice = wallet.erc20_transfer(req_json["from"].lower(), req_json["to"].lower(), req_json["erc20"].lower(), converted_value)
            response = requests.post(rollup_server + "/notice", json={"payload": notice.payload})

        if req_json["method"] == "erc20_withdraw":
            converted_value = int(req_json["amount"]) if isinstance(req_json["amount"], str) and req_json["amount"].isdigit() else req_json["amount"]
            voucher = wallet.erc20_withdraw(req_json["from"].lower(), req_json["erc20"].lower(), converted_value)
            response = requests.post(rollup_server + "/voucher", json={"payload": voucher.payload, "destination": voucher.destination})

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