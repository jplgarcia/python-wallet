from abc import ABC, abstractmethod
from coil_wallet.balance import Balance
from coil_wallet.log import logger
from coil_wallet.util import decode_payload, decode_id_val, encode_function_call, encode_values

class TokenProcessor(ABC):
    """
    Abstract base class for token processors.
    Defines the required interface for any token processor.
    """


    def __init__(self, vault: dict[str: Balance]):
        """
        Initialize the token processor with a reference to a Balance instance.

        Parameters:
            balance (Balance): An instance of the Balance class, which manages asset balances.
        """
        if vault is None: 
            vault = dict[str: Balance]()
        self._vault = vault

    def _balance_get(self, account) -> Balance:
        balance = self._vault.get(account)

        if not balance:
            self._vault[account] = Balance(account)
            balance = self._vault[account]

        return balance

    def balance_get(self, account) -> Balance:
        """Retrieve the balance of all Ether, ERC-20 and ERC-721 tokens for `account`"""

        logger.info(f"Balance for '{account}' retrieved")
        return self._balance_get(account)

    @abstractmethod
    def deposit(self, payload: str):
        """
        Abstract method to handle deposits for the token type.

        Parameters:
            payload (str): The ABI-encoded input data as a hex string.
        """
        pass

    @abstractmethod
    def withdraw(self, account: str, *args):
        """
        Abstract method to handle withdrawals for the token type.

        Parameters:
            account (str): The account from which to withdraw.
            *args: Other parameters specific to the token type.
        """
        pass

    @abstractmethod
    def transfer(self, from_account: str, to_account: str, *args):
        """
        Abstract method to handle transfers for the token type.

        Parameters:
            from_account (str): The account from which to transfer.
            to_account (str): The account to which to transfer.
            *args: Other parameters specific to the token type.
        """
        pass
