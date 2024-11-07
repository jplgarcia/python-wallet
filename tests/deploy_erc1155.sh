#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Step 1: Install Foundry if not installed
# if ! [ -x "$(command -v forge)" ]; then
#   echo "Foundry not installed. Installing Foundry..."
#   curl -L https://foundry.paradigm.xyz | bash
#   foundryup
# else
#   echo "Foundry is already installed."
# fi

# Step 2: Manually set up a new project structure
PROJECT_DIR="erc1155_project"
if [ -d "$PROJECT_DIR" ]; then
  echo "Project directory already exists, skipping project setup..."
else
  echo "Setting up new project structure..."
  mkdir -p $PROJECT_DIR/src $PROJECT_DIR/script $PROJECT_DIR/lib
  cd $PROJECT_DIR
  echo "# foundry.toml - default settings" > foundry.toml
  cd ..
fi

cd $PROJECT_DIR

# Step 3: Install OpenZeppelin Contracts
echo "Installing OpenZeppelin contracts..."
forge install OpenZeppelin/openzeppelin-contracts --no-commit

# Step 4: Create MyERC1155.sol contract
echo "Creating ERC-1155 contract..."
cat <<EOL > src/MyERC1155.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";

contract MyERC1155 is ERC1155 {
    constructor() ERC1155("https://mytokenuri.com/{id}.json") {
        // Mint 10 of token ID 1 to the specified address
        _mint(0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266, 1, 10, "");

        // Mint 5 of token ID 2 to the specified address
        _mint(0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266, 2, 5, "");
    }
}
EOL

# Step 5: Create the deploy script
echo "Creating deployment script..."
cat <<EOL > script/DeployERC1155.s.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Script.sol";
import "../src/MyERC1155.sol";

contract DeployERC1155 is Script {
    function run() external returns (address) {
        // Start broadcasting transactions using the first Anvil account
        vm.startBroadcast();

        // Deploy the ERC-1155 contract
        MyERC1155 myNft = new MyERC1155();
        address contractAddress = address(myNft);

        // End broadcasting transactions
        vm.stopBroadcast();

        // Print the contract address
        console.log("Deployed ERC-1155 contract address:", contractAddress);
        return contractAddress;
    }
}
EOL

# Step 6: Use the correct fixed private key for the default account
PRIVATE_KEY="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
echo "Using fixed private key: $PRIVATE_KEY"

# Step 7: Compile the contract
echo "Compiling the contract..."
forge build

# Step 8: Deploy the contract and print the address
echo "Deploying the contract..."
forge script script/DeployERC1155.s.sol:DeployERC1155 --broadcast --rpc-url http://localhost:8545 --private-key $PRIVATE_KEY

# The script will print the deployed contract address in the console log
