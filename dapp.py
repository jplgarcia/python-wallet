from os import environ
from urllib.parse import urlparse
import requests
import wallet as Wallet
from util import hex_to_str, str_to_hex
import logging
import json

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

rollup_server = environ["ROLLUP_HTTP_SERVER_URL"]
logger.info(f"HTTP rollup_server url is {rollup_server}")

erc20_portal_address = "0x9C21AEb2093C32DDbC53eEF24B873BDCd1aDa1DB" #open(f'./deployments/{network}/ERC20Portal.json')

wallet = Wallet

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

    if msg_sender.lower() == erc20_portal_address.lower():
        try:
            notice = wallet.erc20_deposit_process(payload)
            json_body = vars(notice)
            response = requests.post(rollup_server + "/notice", json=json_body)
            logger.info(f"Received notice status {response.status_code} body {response.content}")
            return "accept"
        except Exception as error:
            error_msg = f"Failed to process ERC20 deposit '{payload}'. {error}"
            logger.debug(error_msg, exc_info=True)
            return "reject"

    else:
        try:
            req_json = decode_json(payload)
            print(req_json)
            if req_json["method"] == "transfer":
                notice = wallet.erc20_transfer(req_json["from"].lower(), req_json["to"].lower(), req_json["erc20"].lower(), req_json["amount"])
                json_body = vars(notice)
                response = requests.post(rollup_server + "/notice", json=json_body)
            if req_json["method"] == "withdraw":
                voucher = wallet.erc20_withdraw(req_json["from"].lower(), req_json["erc20"].lower(), req_json["amount"])
                json_body = vars(voucher)
                response = requests.post(rollup_server + "/voucher", json=json_body)
            return "accept" 
        except Exception as error:
            error_msg = f"Failed to process command '{payload}'. {error}"
            logger.debug(error_msg, exc_info=True)
            return "reject"
            

def handle_inspect(data):
    logger.info(f"Received inspect request data {data}")
    try:
        url = urlparse(hex_to_str(data["payload"]))
        if url.path.startswith("balance/"):
            account = url.path.replace("balance/", "")
            bal = wallet.balance_get(account.lower())
            print(vars(bal))
            report = {"payload": encode(vars(bal))}
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