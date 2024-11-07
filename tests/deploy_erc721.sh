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
PROJECT_DIR="erc721_project"
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

# Step 4: Create MyERC721.sol contract
echo "Creating ERC-721 contract..."
cat <<EOL > src/MyERC721.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

contract MyERC721 is ERC721 {
    constructor() ERC721("MyToken", "MTK") {
        // Mint the token with ID 0 to the specified address
        _mint(0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266, 0);
    }
}
EOL

# Step 5: Create the deploy script
echo "Creating deployment script..."
cat <<EOL > script/DeployERC721.s.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Script.sol";
import "../src/MyERC721.sol";

contract DeployERC721 is Script {
    function run() external returns (address) {
        // Start broadcasting transactions using the first Anvil account
        vm.startBroadcast();

        // Deploy the ERC-721 contract
        MyERC721 myNft = new MyERC721();
        address contractAddress = address(myNft);

        // End broadcasting transactions
        vm.stopBroadcast();

        // Print the contract address
        console.log("Deployed ERC-721 contract address:", contractAddress);
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
forge script script/DeployERC721.s.sol:DeployERC721 --broadcast --rpc-url http://localhost:8545 --private-key $PRIVATE_KEY

# The script will print the deployed contract address in the console log
