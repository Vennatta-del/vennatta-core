import base64
import json
import requests

url = "https://agentcitadel.dev/api/v1/extract-document"
payload = {"document": "test", "fields": ["title"]}

print("[*] Sending initial request to trigger 402 challenge...")
res = requests.post(url, json=payload)
print(f"Status Code: {res.status_code}")

if res.status_code == 402:
    payment_required_b64 = res.headers.get("payment-required")
    if payment_required_b64:
        challenge_json = json.loads(base64.b64decode(payment_required_b64).decode("utf-8"))
        print("\n[+] Captured x402 Challenge Requirements:")
        print(json.dumps(challenge_json, indent=2))
        
        accepts = challenge_json["accepts"][0]
        resource_url = accepts["resource"]
        amount = accepts["amount"]
        asset = accepts["asset"]
        network = accepts["network"]
        pay_to = accepts["payTo"]

        auth_payload = {
            "nonce": "nonce_test_09988377",
            "amount": amount,
            "asset": asset,
            "network": network,
            "payTo": pay_to,
            "resource": resource_url,
            "payer": "0xTestClientWallet123456789"
        }
        
        auth_json_str = json.dumps(auth_payload)
        payment_signature = base64.b64encode(auth_json_str.encode("utf-8")).decode("utf-8")

        print("\n[*] Retrying request with PAYMENT-SIGNATURE header...")
        headers = {
            "Content-Type": "application/json",
            "PAYMENT-SIGNATURE": payment_signature
        }
        
        final_res = requests.post(url, json=payload, headers=headers)
        print(f"Final Status Code: {final_res.status_code}")
        print(f"Payment-Response Header: {final_res.headers.get('payment-response')}")
        print(f"Response Body: {final_res.text}")
    else:
        print("[-] Error: 'payment-required' header missing in 402 response.")
else:
    print(f"[-] Unexpected status code: {res.status_code}")
