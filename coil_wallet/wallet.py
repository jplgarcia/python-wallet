# Copyright 2022 Cartesi Pte. Ltd.
#
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License. You may obtain a copy of the
# License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

import json
from coil_wallet.util import decode_payload, decode_id_val, encode_function_call, encode_values
from coil_wallet.balance import Balance
from coil_wallet.log import logger
from coil_wallet.outputs import Notice, Voucher

ERC20_TRANSFER_FUNCTION_SELECTOR = "transfer(address,uint256)"
ERC721_SAFE_TRANSFER_FROM_SELECTOR = "safeTransferFrom(address,address,uint256)"
ERC1155_SAFE_TRANSFER_FROM_SELECTOR = "safeTransferFrom(address,address,uint256,uint256,bytes)"
ERC1155_SAFE_BATCH_TRANSFER_FROM_SELECTOR = "safeBatchTransferFrom(address,address,uint256[],uint256[],bytes)"

_accounts = dict[str:Balance]()

def accs():
    return _accounts

def _balance_get(account:str) -> Balance:
    balance = _accounts.get(account)

    if not balance:
        _accounts[account] = Balance(account)
        balance = _accounts[account]

    return balance

def balance_get(account:str) -> Balance:
    """Retrieve the balance of all Ether, ERC-20 and ERC-721 tokens for `account`"""

    logger.info(f"Balance for '{account}' retrieved")
    return _balance_get(account)
