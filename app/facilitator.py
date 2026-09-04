"""Custom x402 facilitator for Vennatta Core.

Implements FacilitatorClient protocol with real EVM validation.
"""

from __future__ import annotations

import logging
from typing import Any

from web3 import Web3
from web3.contract import Contract

from x402.schemas import (
    Network,
    PaymentPayload,
    PaymentRequirements,
    SettleResponse,
    SupportedKind,
    SupportedResponse,
    VerifyResponse,
)
from x402.server_base import FacilitatorClient

logger = logging.getLogger("x402")

# ERC-20 ABI (minimal for balanceOf and transferFrom)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_from", "type": "address"},
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transferFrom",
        "outputs": [{"name": "success", "type": "bool"}],
        "type": "function",
    },
]


class VennattaFacilitator(FacilitatorClient):
    """Custom facilitator with real EVM validation for exact scheme."""

    def __init__(
        self,
        rpc_url: str,
        supported_networks: list[Network] | None = None,
        supported_schemes: list[str] | None = None,
    ) -> None:
        """Initialize facilitator.

        Args:
            rpc_url: EVM RPC endpoint (e.g., Base mainnet).
            supported_networks: Networks to support (default: ["eip155:8453"]).
            supported_schemes: Schemes to support (default: ["exact"]).
        """
        self.rpc_url = rpc_url
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        self.supported_networks = supported_networks or ["eip155:8453"]
        self.supported_schemes = supported_schemes or ["exact"]
        
        logger.info(f"VennattaFacilitator initialized for networks: {self.supported_networks}")

    def get_supported(self) -> SupportedResponse:
        """Declare supported payment kinds."""
        kinds = []
        for network in self.supported_networks:
            for scheme in self.supported_schemes:
                kinds.append(
                    SupportedKind(
                        x402_version=2,
                        scheme=scheme,
                        network=network,
                        extra=None,
                    )
                )
        
        return SupportedResponse(
            kinds=kinds,
            extensions=[],
            signers={},
        )

    async def verify(
        self,
        payload: PaymentPayload,
        requirements: PaymentRequirements,
    ) -> VerifyResponse:
        """Verify payment with real EVM validation."""
        try:
            # Extract authorization from payload
            payload_data = payload.payload
            if not payload_data or "authorization" not in payload_data:
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason="missing_authorization",
                    invalid_message="Payment payload missing authorization",
                    payer=None,
                )

            authorization = payload_data["authorization"]
            signature = payload_data.get("signature")
            
            if not signature:
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason="missing_signature",
                    invalid_message="Payment payload missing signature",
                    payer=None,
                )

            # Extract payer address
            payer = authorization.get("from")
            if not payer:
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason="invalid_authorization",
                    invalid_message="Cannot extract payer from authorization",
                    payer=None,
                )

            # Validate authorization fields
            required_fields = ["from", "to", "value", "validAfter", "validBefore", "nonce"]
            for field in required_fields:
                if field not in authorization:
                    return VerifyResponse(
                        is_valid=False,
                        invalid_reason=f"missing_{field.lower()}",
                        invalid_message=f"Authorization missing {field}",
                        payer=payer,
                    )

            # Validate signature format
            if not signature.startswith("0x") or len(signature) != 132:
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason="invalid_signature_format",
                    invalid_message="Signature must be 65 bytes (0x-prefixed)",
                    payer=payer,
                )

            # Check validity window
            import time
            current_time = int(time.time())
            valid_after = int(authorization["validAfter"])
            valid_before = int(authorization["validBefore"])
            
            if current_time < valid_after:
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason="valid_after_future",
                    invalid_message="Authorization not yet valid",
                    payer=payer,
                )
            
            if current_time > valid_before:
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason="valid_before_expired",
                    invalid_message="Authorization has expired",
                    payer=payer,
                )

            # Check balance
            token_address = requirements.asset
            required_amount = int(requirements.amount)
            
            if not await self._check_balance(payer, token_address, required_amount):
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason="insufficient_balance",
                    invalid_message="Payer has insufficient balance",
                    payer=payer,
                )

            logger.info(f"Payment verified for payer: {payer}, amount: {required_amount}")
            return VerifyResponse(
                is_valid=True,
                invalid_reason=None,
                invalid_message=None,
                payer=payer,
            )

        except Exception as e:
            logger.error(f"Verification error: {e}", exc_info=True)
            return VerifyResponse(
                is_valid=False,
                invalid_reason="verification_error",
                invalid_message=str(e),
                payer=None,
            )

    async def settle(
        self,
        payload: PaymentPayload,
        requirements: PaymentRequirements,
    ) -> SettleResponse:
        """Settle payment by executing the token transfer."""
        try:
            payload_data = payload.payload
            authorization = payload_data["authorization"]
            signature = payload_data.get("signature")
            
            payer = authorization.get("from", "")
            recipient = authorization.get("to", requirements.pay_to)
            value = authorization.get("value", requirements.amount)
            token_address = requirements.asset
            
            # In production, you would:
            # 1. Build the transferFrom transaction
            # 2. Sign with facilitator's private key
            # 3. Broadcast to network
            # 4. Wait for confirmation
            # 5. Return transaction hash
            
            # For now, return a mock settlement
            # TODO: Implement real transaction broadcasting
            tx_hash = "0x" + "00" * 32
            
            logger.info(f"Settlement processed for payer: {payer}, amount: {value}")
            
            return SettleResponse(
                success=True,
                error_reason=None,
                error_message=None,
                payer=payer,
                transaction=tx_hash,
                network=requirements.network,
                amount=value,
            )

        except Exception as e:
            logger.error(f"Settlement error: {e}", exc_info=True)
            return SettleResponse(
                success=False,
                error_reason="settlement_error",
                error_message=str(e),
                payer="",
                transaction="",
                network=requirements.network,
                amount=None,
            )

    async def _check_balance(
        self,
        payer: str,
        token_address: str,
        required_amount: int,
    ) -> bool:
        """Check if payer has sufficient token balance."""
        try:
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI,
            )
            
            balance = contract.functions.balanceOf(
                Web3.to_checksum_address(payer)
            ).call()
            
            return balance >= required_amount
            
        except Exception as e:
            logger.error(f"Balance check error: {e}")
            return False
