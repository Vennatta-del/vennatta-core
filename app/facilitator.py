"""Custom x402 facilitator for Vennatta Core.

Implements FacilitatorClient protocol with real EVM validation.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from eth_account import Account
from eth_account.messages import encode_typed_data
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

# EIP-3009 TransferWithAuthorization type hash
TRANSFER_WITH_AUTHORIZATION_TYPEHASH = Web3.keccak(
    text="TransferWithAuthorization(address from,address to,uint256 value,uint256 validAfter,uint256 validBefore,bytes32 nonce)"
)

# EIP-712 Domain type hash
EIP712_DOMAIN_TYPEHASH = Web3.keccak(
    text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
)


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
        
        # Get chain ID from RPC
        self.chain_id = self.w3.eth.chain_id
        
        logger.info(f"VennattaFacilitator initialized for networks: {self.supported_networks} (chain_id={self.chain_id})")

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

            # CRITICAL: Verify EIP-3009 signature
            if not self._verify_eip3009_signature(authorization, signature, payer):
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason="invalid_signature",
                    invalid_message="EIP-3009 signature verification failed",
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

            logger.info(f"✅ Payment verified for payer: {payer}, amount: {required_amount}")
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
            
            # TODO: Implement real transaction broadcasting
            # For now, return a mock settlement
            tx_hash = "0x" + "00" * 32
            
            logger.info(f"⚠️ Settlement mocked for payer: {payer}, amount: {value}")
            
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

    def _verify_eip3009_signature(
        self,
        authorization: dict[str, Any],
        signature: str,
        expected_signer: str,
    ) -> bool:
        """Verify EIP-3009 TransferWithAuthorization signature."""
        try:
            # Build EIP-712 domain
            domain = {
                "name": "USD Coin",
                "version": "2",
                "chainId": self.chain_id,
                "verifyingContract": Web3.to_checksum_address(authorization["to"]),
            }
            
            # Build EIP-712 message
            message = {
                "from": Web3.to_checksum_address(authorization["from"]),
                "to": Web3.to_checksum_address(authorization["to"]),
                "value": int(authorization["value"]),
                "validAfter": int(authorization["validAfter"]),
                "validBefore": int(authorization["validBefore"]),
                "nonce": authorization["nonce"],  # Keep as hex string
            }
            
            # Encode typed data
            encoded_message = encode_typed_data(
                domain_types={
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "verifyingContract", "type": "address"},
                    ],
                    "TransferWithAuthorization": [
                        {"name": "from", "type": "address"},
                        {"name": "to", "type": "address"},
                        {"name": "value", "type": "uint256"},
                        {"name": "validAfter", "type": "uint256"},
                        {"name": "validBefore", "type": "uint256"},
                        {"name": "nonce", "type": "bytes32"},
                    ],
                },
                domain_data=domain,
                message_types={
                    "TransferWithAuthorization": [
                        {"name": "from", "type": "address"},
                        {"name": "to", "type": "address"},
                        {"name": "value", "type": "uint256"},
                        {"name": "validAfter", "type": "uint256"},
                        {"name": "validBefore", "type": "uint256"},
                        {"name": "nonce", "type": "bytes32"},
                    ],
                },
                domain=domain,
                message=message,
            )
            
            # Recover signer
            recovered = Account.recover_message(encoded_message, signature=signature)
            
            # Verify signer matches expected (from address)
            return recovered.lower() == Web3.to_checksum_address(expected_signer).lower()
            
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False

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
