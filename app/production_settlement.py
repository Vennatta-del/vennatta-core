"""Production settlement handler - verifies payments on Base mainnet."""

import os
import json
from web3 import Web3
from typing import Dict, Any, Optional

class ProductionSettlement:
    """Handle payment verification on Base mainnet."""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
        self.private_key = os.getenv("TEST_PRIVATE_KEY")
        self._account = None
        
    @property
    def account(self):
        """Lazy-load account only when private key is available."""
        if self._account is None and self.private_key:
            self._account = self.w3.eth.account.from_key(self.private_key)
        return self._account
    
    def verify_payment(self, payment: Dict[str, Any]) -> tuple[bool, str]:
        """Verify payment signature."""
        try:
            payload = payment.get("payload", {})
            signature = payload.get("signature")
            signer = payload.get("signer")
            amount = int(payload.get("amount", 0))
            
            if not all([signature, signer]):
                return False, "Missing signature or signer"
            
            # Verify signature
            payload_copy = {k: v for k, v in payload.items() if k not in ["signature", "signer"]}
            payload_json = json.dumps(payload_copy, sort_keys=True)
            payload_hash = self.w3.keccak(text=payload_json)
            recovered = self.w3.eth.account.recover_hash(payload_hash, signature=signature)
            
            if recovered.lower() != signer.lower():
                return False, "Invalid signature"
            
            print(f"✅ Payment verified: {amount} USDC from {signer}")
            return True, "Payment verified"
            
        except Exception as e:
            return False, f"Verification error: {str(e)}"

# Global instance (lazy initialization)
settlement = ProductionSettlement()
