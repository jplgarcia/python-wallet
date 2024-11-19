# from eth_utils import function_signature_to_4byte_selector
# from eth_abi import decode, encode
# from typing import List, Tuple, Any

# data = "000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000140000000000000000000000000000000000000000000000000000000000000016000000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"

# def decode_payload(types: List[str], payload: str, ) -> Tuple[Any, ...]:
#     """
#     Decodes an ABI-encoded payload.

#     Args:
#         types (List[str]): A list of ABI types as strings.
#         payload (str): The hex-encoded payload to decode.

#     Returns:
#         Tuple[Any, ...]: A tuple containing the decoded values.
#     """
#     # Ensure the payload is in bytes format
#     payload_bytes = bytes.fromhex(payload[2:])  # Remove '0x' prefix and convert to bytes
#     return decode(types, payload_bytes)

# def decode_id_val(payload: str) -> Tuple[Any, ...]:
#     return decode(['uint256[]', 'uint256[]'], payload)

# print('0x' + data[:128])
# main_structure = decode_payload(['uint256', 'uint256'], '0x' + data[:128])

# first_array_start = main_structure[0]*2
# second_array_start = main_structure[1]*2

# print("main")
# print(main_structure*2)

# # Step 3: Decode the first array's length and elements
# first_array_length = decode_payload(['uint256'], '0x' + data[first_array_start:first_array_start+64])[0]
# first_array_elements = decode_payload(['uint256'] * first_array_length, '0x' + data[first_array_start+64:first_array_start+64+64*first_array_length])

# # Step 4: Decode the second array's length and elements
# second_array_length = decode_payload(['uint256'], '0x' + data[second_array_start:second_array_start+64])[0]
# second_array_elements = decode_payload(['uint256'] * second_array_length, '0x' + data[second_array_start+64:second_array_start+64+64*second_array_length])

# # Print the decoded arrays
# print("First Array (IDs):", first_array_elements)
# print("Second Array (Values):", second_array_elements)


from web3 import Web3

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
account = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
private_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
to = "0x0000000000000000000000000000000000000000"  # Burn address
value = w3.to_wei(1, "ether")
