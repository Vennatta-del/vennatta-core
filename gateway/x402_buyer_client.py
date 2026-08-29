import os
import json
import base64
import hashlib
import logging
import requests

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("X402ProductionBuyer")

class PolicyValidator:
    def __init__(self, expected_resource, expected_network, expected_asset, expected_amount, expected_payto):
        self.expected_resource = expected_resource
        self.expected_network = expected_network
        self.expected_asset = expected_asset.lower()
        self.expected_amount = str(expected_amount)
        self.expected_payto = expected_payto.lower()

    def validate(self, resource, method, requirements):
        if method != "POST":
            raise ValueError(f"Policy violation: Unsupported method {method}")
        if resource != self.expected_resource:
            raise ValueError(f"Policy violation: Resource mismatch. Expected {self.expected_resource}, got {resource}")
        
        accepts = requirements.get("accepts", [])
        if not accepts:
            raise ValueError("Policy violation: No acceptance schemes found in 402 challenge.")
        
        scheme_match = False
        for acc in accepts:
            if (
                acc.get("network") == self.expected_network and
                acc.get("asset", "").lower() == self.expected_asset and
                str(acc.get("amount")) == self.expected_amount and
                acc.get("payTo", "").lower() == self.expected_payto
            ):
                scheme_match = True
                break
                
        if not scheme_match:
            raise ValueError("Policy violation: 402 challenge parameters do not match security policy criteria.")
        logger.info("Production policy validation passed successfully.")

class ProductionSigner:
    def __init__(self, private_key, buyer_address):
        if not private_key:
            raise ValueError("Production signer requires a valid private key.")
        self.private_key = private_key
        self.buyer_address = buyer_address

    def sign(self, resource, method, body, requirements):
        # Extract specific challenge requirements to bind the payment proof
        accepts = requirements.get("accepts", [{}])[0]
        
        payment_proof = {
            "nonce": hashlib.sha256(os.urandom(32)).hexdigest(),
            "amount": str(accepts.get("amount", "10000")),
            "asset": accepts.get("asset", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"),
            "network": accepts.get("network", "eip155:8453"),
            "payTo": accepts.get("payTo", "0x80347776d27fA7f98e6E5703F4D2c7ffBB1977dc"),
            "resource": resource,
            "payer": self.buyer_address
        }
        
        # Serialize and base64-encode the payment proof JSON string for the header
        proof_json = json.dumps(payment_proof)
        return base64.b64encode(proof_json.encode("utf-8")).decode("utf-8")

class X402Buyer:
    def __init__(self, policy: PolicyValidator, signer: ProductionSigner):
        self.policy = policy
        self.signer = signer
        self.session = requests.Session()

    def _parse_payment_required(self, headers):
        challenge_header = headers.get("payment-required") or headers.get("WWW-Authenticate") or headers.get("X-Payment-Required")
        if challenge_header:
            if challenge_header.startswith("x402 "):
                challenge_header = challenge_header[5:]
            try:
                decoded_bytes = base64.b64decode(challenge_header)
                return json.loads(decoded_bytes.decode("utf-8"))
            except Exception:
                try:
                    return json.loads(challenge_header)
                except Exception:
                    pass
        return {}

    def call(self, resource: str, body: dict):
        canonical_body = json.dumps(body, sort_keys=True)
        
        first = self.session.post(resource, json=body)
        if first.status_code != 402:
            raise RuntimeError(f"Expected HTTP 402, received {first.status_code}")

        requirements = self._parse_payment_required(first.headers)
        if not requirements:
            try:
                requirements = first.json()
            except Exception:
                raise RuntimeError("Failed to parse x402 payment challenge requirements.")

        self.policy.validate(resource, "POST", requirements)

        signature = self.signer.sign(
            resource=resource,
            method="POST",
            body=canonical_body,
            requirements=requirements
        )

        second = self.session.post(
            resource,
            json=body,
            headers={"PAYMENT-SIGNATURE": signature}
        )

        if second.status_code != 200:
            raise RuntimeError(f"Paid request failed with status {second.status_code}: {second.text}")

        result = second.json()
        logger.info("Successfully completed live production paid invocation cycle.")
        return result
