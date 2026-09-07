"""EVM Facilitator for Vennatta Core x402 payments."""

from __future__ import annotations

import logging
from typing import Any
from eth_account import Account
from eth_account.messages import encode_defunct
import hashlib

logger = logging.getLogger(__name__)


class EvmFacilitator:
    """EVM payment facilitator for x402 protocol.

    Handles USDC payments on EVM chains (Base, Ethereum, etc.).
    """

    def __init__(
        self,
        rpc_url: str = "https://mainnet.base.org",
        supported_networks: list[str] | None = None,
    ):
        """Initialize EVM facilitator.

        Args:
            rpc_url: EVM RPC endpoint
            supported_networks: List of supported network IDs (e.g., eip155:8453 for Base)
        """
        self.rpc_url = rpc_url
        self.supported_networks = supported_networks or [
            "eip155:8453",  # Base
            "eip155:1",     # Ethereum mainnet
        ]
        logger.info(f"⚡ EvmFacilitator initialized with RPC: {rpc_url}")
        logger.info(f"⚡ Supported networks: {self.supported_networks}")

    def verify_payment(
        self,
        payload: dict[str, Any],
        requirements: dict[str, Any],
    ) -> dict[str, Any]:
        """Verify an EVM payment.

        Args:
            payload: Payment payload with signature and authorization
            requirements: Payment requirements (amount, asset, recipient)

        Returns:
            Verification result dict
        """
        try:
            logger.info("⚡⚡⚡ EVM verify_payment() called ⚡⚡⚡")
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

            # Validate network is supported
            network = requirements.get("network")
            if network and network not in self.supported_networks:
                logger.warning(f"❌ Unsupported network: {network}")
                return {
                    "is_valid": False,
                    "invalid_reason": "unsupported_network",
                    "invalid_message": f"Network {network} not supported",
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

            # Verify signature format (EVM signatures are 0x-prefixed, 132 chars = 65 bytes)
            if not self._verify_signature_format(signature):
                logger.warning(f"❌ Invalid signature format: {signature[:20]}...")
                return {
                    "is_valid": False,
                    "invalid_reason": "invalid_signature_format",
                    "invalid_message": "Invalid signature format",
                    "payer": payer,
                }

            # Verify signature cryptographically
            if not self._verify_signature_cryptographic(signature, authorization, requirements):
                logger.warning(f"❌ Cryptographic signature verification failed")
                return {
                    "is_valid": False,
                    "invalid_reason": "invalid_signature",
                    "invalid_message": "Signature does not match payer address",
                    "payer": payer,
                }

            logger.info("  ✅ All validation passed")
            logger.info(f"  ✅ EVM payment VERIFIED: {payer}, {amount}")

            return {
                "is_valid": True,
                "invalid_reason": None,
                "invalid_message": None,
                "payer": payer,
            }

        except Exception as e:
            logger.error(f"❌❌❌ EVM verification EXCEPTION: {e} ❌❌❌")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "is_valid": False,
                "invalid_reason": "verification_error",
                "invalid_message": str(e),
                "payer": None,
            }

    def _verify_signature_format(self, signature: str) -> bool:
        """Verify EVM signature format.

        EVM signatures are 0x-prefixed, 132 character hex strings (65 bytes).
        """
        try:
            if not signature:
                return False

            # Must start with 0x
            if not signature.startswith("0x"):
                return False

            # Remove 0x prefix
            sig_hex = signature[2:]

            # Must be 130 hex chars (65 bytes)
            if len(sig_hex) != 130:
                return False

            # Must be valid hex
            bytes.fromhex(sig_hex)

            return True
        except Exception:
            return False

    def _verify_signature_cryptographic(
        self,
        signature: str,
        authorization: dict[str, Any],
        requirements: dict[str, Any],
    ) -> bool:
        """Verify EVM signature cryptographically.

        Recovers the signer address from the signature and verifies it matches the payer.

        Args:
            signature: 0x-prefixed signature
            authorization: Authorization data that was signed
            requirements: Payment requirements

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Extract payer address
            payer = authorization.get("payer") or authorization.get("from")
            if not payer:
                logger.warning("Cannot extract payer for signature verification")
                return False

            # Reconstruct the message that was signed
            # x402 signs: "Pay {amount} {asset} to {payTo} on {network}"
            amount = requirements.get("amount", "0")
            asset = requirements.get("asset", "USDC")
            pay_to = requirements.get("payTo", "")
            network = requirements.get("network", "")

            # Format message (must match what the client signed)
            message = f"Pay {amount} {asset} to {pay_to} on {network}"
            logger.info(f"  Reconstructed message: {message}")

            # Hash the message (EIP-191 personal sign)
            message_hash = encode_defunct(text=message)

            # Recover signer address from signature
            recovered_address = Account.recover_message(message_hash, signature=signature)
            logger.info(f"  Recovered address: {recovered_address}")
            logger.info(f"  Expected payer: {payer}")

            # Compare (case-insensitive)
            if recovered_address.lower() == payer.lower():
                logger.info("  ✅ Signature matches payer address!")
                return True
            else:
                logger.warning(f"  ❌ Signature mismatch: {recovered_address} != {payer}")
                return False

        except Exception as e:
            logger.error(f"  Cryptographic verification error: {e}")
            return False

    def get_supported(self) -> dict[str, Any]:
        """Get supported payment kinds.

        Returns:
            Dict with supported networks and schemes
        """
        return {
            "kinds": [
                {
                    "network": network,
                    "scheme": "exact",
                    "version": "2",
                }
                for network in self.supported_networks
            ],
        }

    def settle(
        self,
        payload: dict[str, Any],
        requirements: dict[str, Any],
    ) -> dict[str, Any]:
        """Settle an EVM payment.

        In production, this would:
        1. Verify the payment on-chain
        2. Mark the payment as settled
        3. Return transaction receipt

        For now, we return a mock settlement.

        Args:
            payload: Payment payload
            requirements: Payment requirements

        Returns:
            Settlement result
        """
        logger.info("⚠️ EVM settle() called")
        try:
            payer = payload.get("payload", {}).get("authorization", {}).get("payer", "")
            amount = requirements.get("amount", "0")

            logger.info(f"⚠️ EVM settlement: {payer}, {amount}")

            # In production, this would:
            # - Call the x402 contract to verify settlement
            # - Return the actual transaction hash
            # For now, return mock data

            return {
                "success": True,
                "error_reason": None,
                "error_message": None,
                "payer": payer,
                "transaction": "0x" + "00" * 32,  # Mock transaction hash
                "network": requirements.get("network", "eip155:8453"),
                "amount": amount,
            }
        except Exception as e:
            logger.error(f"EVM settlement error: {e}")
            return {
                "success": False,
                "error_reason": "settlement_error",
                "error_message": str(e),
                "payer": "",
                "transaction": "",
                "network": "eip155:8453",
                "amount": None,
            }


# Test the facilitator
if __name__ == "__main__":
    facilitator = EvmFacilitator()

    # Test payment
    payload = {
        "payload": {
            "authorization": {"payer": "0xE7d7BdF214E23A8fD1ED22e476BF742862a70212"},
            "signature": "0x" + "00" * 130,  # Mock signature
        },
    }
    requirements = {
        "network": "eip155:8453",
        "asset": "USDC",
        "amount": "10000",
        "payTo": "0x1234567890123456789012345678901234567890",
    }

    result = facilitator.verify_payment(payload, requirements)
    print(f"Test result: {result}")
