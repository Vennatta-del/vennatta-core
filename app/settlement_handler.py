"""Simple on-chain settlement handler for x402 payments."""

import json
from web3 import Web3
from typing import Dict, Any

class SimpleSettlementHandler:
    """Handle x402 payment settlement on Base mainnet."""
    
    def __init__(self, private_key: str, network: str = "eip155:8453"):
        self.w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
        self.account = self.w3.eth.account.from_key(private_key)
        self.network = network
        
    def verify_payment(self, payment: Dict[str, Any]) -> bool:
        """Verify payment signature and details."""
        try:
            # Extract payment details
            payload = payment.get("payload", {})
            signature = payload.get("signature")
            signer = payload.get("signer")
            
            if not all([signature, signer]):
                return False
            
            # Verify signature
            payload_copy = {k: v for k, v in payload.items() if k not in ["signature", "signer"]}
            payload_json = json.dumps(payload_copy, sort_keys=True)
            payload_hash = self.w3.keccak(text=payload_json)
            
            recovered = self.w3.eth.account.recover_hash(payload_hash, signature=signature)
            
            return recovered.lower() == signer.lower()
            
        except Exception as e:
            print(f"Verification error: {e}")
            return False
    
    def settle_payment(self, payment: Dict[str, Any]) -> str:
        """Settle payment (in production, this would transfer USDC)."""
        # For now, just log the payment
        payload = payment.get("payload", {})
        amount = payload.get("amount", "0")
        resource = payload.get("resource", "unknown")
        
        print(f"💰 Payment settled: {amount} for {resource}")
        
        # Return transaction hash (in production, this would be real TX)
        return "0x" + "00" * 32  # Placeholder
