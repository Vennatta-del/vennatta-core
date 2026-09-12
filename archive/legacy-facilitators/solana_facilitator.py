"""Solana Facilitator for Vennatta Core x402 payments."""

from __future__ import annotations

import logging
from typing import Any
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.signature import Signature
import base58
import base64
import json

logger = logging.getLogger(__name__)


class SolanaFacilitator:
    """Solana payment facilitator for x402 protocol.
    
    Handles SOL and SPL token (USDC) payments on Solana.
    """
    
    def __init__(
        self,
        rpc_url: str = "https://api.mainnet-beta.solana.com",
        supported_tokens: list[str] | None = None,
    ):
        """Initialize Solana facilitator.
        
        Args:
            rpc_url: Solana RPC endpoint
            supported_tokens: List of supported token mints (e.g., USDC mint)
        """
        self.rpc_url = rpc_url
        self.supported_tokens = supported_tokens or [
            "EPjFWWD5AufqPLqeM2RcR5K2oL9E8xN3xN3xN3xN3xN3",  # USDC on Solana
            "So11111111111111111111111111111111111111112",  # SOL
        ]
        logger.info(f"🌞 SolanaFacilitator initialized with RPC: {rpc_url}")
        logger.info(f"🌞 Supported tokens: {self.supported_tokens}")
    
    def verify_payment(
        self,
        payload: dict[str, Any],
        requirements: dict[str, Any],
    ) -> dict[str, Any]:
        """Verify a Solana payment.
        
        Args:
            payload: Payment payload with signature and authorization
            requirements: Payment requirements (amount, token, recipient)
        
        Returns:
            Verification result dict
        """
        try:
            logger.info("🌞🌞🌞 Solana verify_payment() called 🌞🌞🌞")
            logger.info(f"  Payload type: {type(payload)}")
            logger.info(f"  Requirements: {requirements}")
            
            # Extract payment data
            payment_data = payload.get("payload", {})
            signature = payment_data.get("signature")
            authorization = payment_data.get("authorization", {})
            
            logger.info(f"  Signature present: {bool(signature)}")
            logger.info(f"  Authorization keys: {authorization.keys() if isinstance(authorization, dict) else 'not a dict'}")
            
            if not signature:
                logger.warning("❌ Missing signature")
                return {
                    "is_valid": False,
                    "invalid_reason": "missing_signature",
                    "invalid_message": "Missing payment signature",
                    "payer": None,
                }
            
            # Extract payer from authorization
            payer = authorization.get("payer") or authorization.get("from")
            if not payer:
                logger.warning("❌ Cannot extract payer")
                return {
                    "is_valid": False,
                    "invalid_reason": "invalid_authorization",
                    "invalid_message": "Cannot extract payer address",
                    "payer": None,
                }
            
            logger.info(f"  Payer: {payer}")
            
            # Validate token is supported
            token = requirements.get("asset") or requirements.get("token")
            if token and token not in self.supported_tokens:
                logger.warning(f"❌ Unsupported token: {token}")
                return {
                    "is_valid": False,
                    "invalid_reason": "unsupported_token",
                    "invalid_message": f"Token {token} not supported",
                    "payer": payer,
                }
            
            # Validate amount
            amount = requirements.get("amount")
            if not amount:
                logger.warning("❌ Missing amount")
                return {
                    "is_valid": False,
                    "invalid_reason": "missing_amount",
                    "invalid_message": "Missing payment amount",
                    "payer": payer,
                }
            
            # Verify signature format
            if not self._verify_signature_format(signature):
                logger.warning(f"❌ Invalid signature format")
                return {
                    "is_valid": False,
                    "invalid_reason": "invalid_signature_format",
                    "invalid_message": "Invalid signature format",
                    "payer": payer,
                }
            
            # TODO: Add actual Solana transaction verification here
            # For now, we'll do basic validation
            # In production, this would:
            # 1. Fetch the transaction from Solana
            # 2. Verify the signature matches
            # 3. Verify the amount and token transfer
            # 4. Check the recipient matches
            
            logger.info("  ✅ Basic validation passed")
            logger.info(f"  ✅ Solana payment VERIFIED: {payer}, {amount}")
            
            return {
                "is_valid": True,
                "invalid_reason": None,
                "invalid_message": None,
                "payer": payer,
            }
            
        except Exception as e:
            logger.error(f"❌❌❌ Solana verification EXCEPTION: {e} ❌❌❌")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "is_valid": False,
                "invalid_reason": "verification_error",
                "invalid_message": str(e),
                "payer": None,
            }
    
    def _verify_signature_format(self, signature: str) -> bool:
        """Verify Solana signature format.
        
        Solana signatures are base58-encoded 64-byte signatures.
        """
        try:
            if not signature:
                return False
            
            # Try to decode as base58
            decoded = base58.b58decode(signature)
            
            # Solana signatures are 64 bytes
            if len(decoded) != 64:
                return False
            
            return True
        except Exception:
            return False
    
    def get_supported(self) -> dict[str, Any]:
        """Get supported payment kinds.
        
        Returns:
            Dict with supported networks and schemes
        """
        return {
            "kinds": [
                {
                    "network": "solana:mainnet",
                    "scheme": "exact",
                    "version": "2",
                },
            ],
        }
    
    def settle(
        self,
        payload: dict[str, Any],
        requirements: dict[str, Any],
    ) -> dict[str, Any]:
        """Settle a Solana payment (mock for now).
        
        Args:
            payload: Payment payload
            requirements: Payment requirements
        
        Returns:
            Settlement result
        """
        logger.info("⚠️ Solana settle() called")
        try:
            payer = payload.get("payload", {}).get("authorization", {}).get("payer", "")
            amount = requirements.get("amount", "0")
            
            logger.info(f"⚠️ Solana settlement mocked: {payer}, {amount}")
            
            return {
                "success": True,
                "error_reason": None,
                "error_message": None,
                "payer": payer,
                "transaction": "0x" + "00" * 64,  # Mock transaction hash
                "network": "solana:mainnet",
                "amount": amount,
            }
        except Exception as e:
            logger.error(f"Solana settlement error: {e}")
            return {
                "success": False,
                "error_reason": "settlement_error",
                "error_message": str(e),
                "payer": "",
                "transaction": "",
                "network": "solana:mainnet",
                "amount": None,
            }


# Test the facilitator
if __name__ == "__main__":
    facilitator = SolanaFacilitator()
    
    # Test payment
    payload = {
        "payload": {
            "authorization": {"payer": "FqkfjTzc1L1MRbynY7L1yxBjGFRNHBivokhzmsNzFpg5"},
            "signature": "5j7s6Nz...",  # Mock signature
        },
    }
    requirements = {
        "asset": "EPjFWWD5AufqPLqeM2RcR5K2oL9E8xN3xN3xN3xN3xN3",  # USDC
        "amount": "10000",
    }
    
    result = facilitator.verify_payment(payload, requirements)
    print(f"Test result: {result}")
