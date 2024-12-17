"""
The `get_blockchain.py` file retrieves the current state of the blockchain 
from the Ledger Manager's API server. It sends an HTTP GET request to the 
`/get_blockchain` endpoint and prints the response.

Key functionalities:
1. **Requests blockchain data**: Uses the `requests` library to communicate with 
   the Ledger Manager's REST API.
2. **Formats the response**: Formats the blockchain data received into a readable JSON structure.

This file is typically used as a client utility for viewing the latest blockchain state.
"""
import requests
import json

url = 'http://localhost:8080/get_blockchain'

response = requests.get(url)

print("Response Status Code:", response.status_code)
print("Response Content:")
print(json.dumps(response.json(), indent=4))
