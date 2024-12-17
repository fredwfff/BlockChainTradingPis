# This script retrieves the balance for a specific public key from the ledger manager.
# It does so by:
# 1. Loading the public key from a local 'public_key.pem' file.
# 2. URL-encoding the public key to make it suitable for inclusion in an HTTP GET request.
# 3. Sending a GET request to the ledger manager's '/get_balance' endpoint, which responds
#    with the balance associated with the provided public key.
# 4. Printing the HTTP response status code and the balance content for the user.

import requests
import urllib.parse

with open('public_key.pem', 'rb') as f:
    public_key = f.read().decode('utf-8')

public_key_encoded = urllib.parse.quote(public_key)

url = f'http://localhost:8080/get_balance?public_key={public_key_encoded}'

response = requests.get(url)

print("Response Status Code:", response.status_code)
print("Response Content:", response.text)
