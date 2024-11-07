class Balance():
    """
    Holds and manipulates an account's balance for Ether, ERC-20, ERC-721, and ERC-1155 tokens
    """

    def __init__(self, account: str,
                 ether: int = 0,
                 erc20: dict[str: int] = None,
                 erc721: dict[str: set[int]] = None,
                 erc1155: dict[str: dict[int: int]] = None):
        self._account = account
        self._ether = ether if ether else 0
        self._erc20 = erc20 if erc20 else {}
        self._erc721 = erc721 if erc721 else {}
        self._erc1155 = erc1155 if erc1155 else {}

    
    def ether_get(self) -> int :
        return self._ether
    
    def _ether_increase(self, amount:int) :
        if amount < 0:
            raise ValueError(
                f"Failed to increase ether balance for {self._account}. "
                f"{amount} should be a positive number")

        self._ether = self._ether + amount
    
    def _ether_decrease(self, amount:int) :
        if amount < 0:
            raise ValueError(
                f"Failed to increase ether balance for {self._account}. "
                f"{amount} should be a positive number")

        if self._ether < amount:
            raise ValueError(
                f"Failed to decrease ether balance for {self._account}. "
                f"Not enough funds to decrease {amount}")

        self._ether = self._ether - amount

    def erc20_get(self, erc20: str) -> int:
        return self._erc20.get(erc20, 0)

    def _erc20_increase(self, erc20: str, amount: int):
        if amount < 0:
            raise ValueError(
                f"Failed to increase {erc20} balance for {self._account}. "
                f"{amount} should be a positive number")

        self._erc20[erc20] = self._erc20.get(erc20, 0) + amount

    def _erc20_decrease(self, erc20: str, amount: int):
        if amount < 0:
            raise ValueError(
                f"Failed to decrease {erc20} balance for {self._account}. "
                f"{amount} should be a positive number")

        erc20_balance = self._erc20.get(erc20, 0)
        if erc20_balance < amount:
            raise ValueError(
                f"Failed to decrease {erc20} balance for {self._account}. "
                f"Not enough funds to decrease {amount}")

        self._erc20[erc20] = erc20_balance - amount

    def erc721_get(self, erc721: str) -> set[int]:
        return self._erc721.get(erc721, set())

    def _erc721_add(self, erc721: str, token_id: int):
        tokens = self._erc721.get(erc721)
        if tokens:
            tokens.add(token_id)
        else:
            self._erc721[erc721] = {token_id}
            tokens = self._erc721.get(erc721)
            tokens.add(token_id)

    def _erc721_remove(self, erc721: str, token_id: int):
        tokens = self._erc721.get(erc721, set())
        try:
            tokens.remove(token_id)
        except KeyError as error:
            raise ValueError(
                "Failed to remove token"
                f"'ERC-721: {erc721}, id: {token_id}' from {self._account}. "
                "Account doesn't own token") from error
    # ERC-1155 related methods
    def erc1155_get(self, erc1155: str, token_id: int) -> int:
        """
        Get the balance of a specific ERC-1155 token ID.
        """
        return self._erc1155.get(erc1155, {}).get(token_id, 0)

    def _erc1155_increase(self, erc1155: str, token_id: int, amount: int):
        """
        Increase the balance of a specific ERC-1155 token ID.
        """
        if amount < 0:
            raise ValueError(
                f"Failed to increase balance for ERC-1155 {erc1155}, token ID {token_id}. "
                f"{amount} should be a positive number"
            )

        if erc1155 not in self._erc1155:
            self._erc1155[erc1155] = {}
        
        current_balance = self._erc1155[erc1155].get(token_id, 0)
        self._erc1155[erc1155][token_id] = current_balance + amount

    def _erc1155_decrease(self, erc1155: str, token_id: int, amount: int):
        """
        Decrease the balance of a specific ERC-1155 token ID.
        """
        if amount < 0:
            raise ValueError(
                f"Failed to decrease balance for ERC-1155 {erc1155}, token ID {token_id}. "
                f"{amount} should be a positive number"
            )

        current_balance = self._erc1155.get(erc1155, {}).get(token_id, 0)
        if current_balance < amount:
            raise ValueError(
                f"Failed to decrease balance for ERC-1155 {erc1155}, token ID {token_id}. "
                f"Not enough funds to decrease {amount}"
            )

        self._erc1155[erc1155][token_id] = current_balance - amount
