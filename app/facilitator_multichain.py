"""Multi-Chain Vennatta Facilitator for x402 payments.

Supports:
- EVM (Base, Ethereum, etc.)
- Solana (SOL, USDC)
- Future: DAG/Sonic
"""

from __future__ import annotations

import logging
import time
import traceback
from typing import Any

from eth_account import Account
from web3 import Web3

from x402.schemas import PaymentPayload, PaymentRequirements, VerifyResponse, SettleResponse

from .solana_facilitator import SolanaFacilitator

logger = logging.getLogger(__name__)


class VennattaFacilitator:
    """Multi-chain payment facilitator for Vennatta Core.
    
    Routes payments to appropriate chain handler:
    - EVM payments → EVM handler (existing logic)
    - Solana payments → Solana handler
    - Future: DAG/Sonic → DAG handler
    """
    
    def __init__(
        self,
        rpc_url: str,
        supported_networks: list[str] | None = None,
        supported_schemes: list[str] | None = None,
    ):
        """Initialize multi-chain facilitator.
        
        Args:
            rpc_url: EVM RPC URL (for EVM chains)
            supported_networks: List of supported EVM networks
            supported_schemes: List of supported payment schemes
        """
        # EVM setup
        self.rpc_url = rpc_url
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.supported_networks = supported_networks or ["eip155:8453"]  # Base
        self.supported_schemes = supported_schemes or ["exact"]
        
        # Extract chain ID from network
        if self.supported_networks:
            network = self.supported_networks[0]
            # Parse chain ID from "eip155:8453" format
            if ":" in network:
                self.chain_id = int(network.split(":")[1])
            else:
                self.chain_id = 8453  # Default to Base
        else:
            self.chain_id = 8453
        
        # Solana setup
        self.solana_facilitator = SolanaFacilitator(
            rpc_url="https://api.mainnet-beta.solana.com",
        )
        
        logger.info(f"👑 VennattaFacilitator (Multi-Chain) initialized!")
        logger.info(f"  EVM RPC: {rpc_url}")
        logger.info(f"  Supported EVM networks: {self.supported_networks}")
        logger.info(f"  Supported schemes: {self.supported_schemes}")
        logger.info(f"  Chain ID: {self.chain_id}")
        logger.info(f"  Solana RPC: https://api.mainnet-beta.solana.com")
    
    def get_supported(self) -> Any:
        """Get supported payment kinds across all chains.
        
        Returns:
            SupportedResponse with all supported networks/schemes
        """
        from x402.schemas import SupportedResponse, SupportedKind
        
        kinds = []
        
        # Add EVM networks
        for network in self.supported_networks:
            for scheme in self.supported_schemes:
                kinds.append(
                    SupportedKind(
                        network=network,
                        scheme=scheme,
                        version="2",
                    )
                )
        
        # Add Solana
        kinds.append(
            SupportedKind(
                network="solana:mainnet",
                scheme="exact",
                version="2",
            )
        )
        
        logger.info(f"📦 get_supported() returning {len(kinds)} kinds")
        for kind in kinds:
            logger.info(f"  - {kind.network} / {kind.scheme}")
        
        return SupportedResponse(kinds=kinds)
    
    async def verify(
        self,
        payload: PaymentPayload,
        requirements: PaymentRequirements,
    ) -> VerifyResponse:
        """Verify payment - routes to appropriate chain handler.
        
        Args:
            payload: Payment payload
            requirements: Payment requirements
        
        Returns:
            VerifyResponse with verification result
        """
        logger.info(f"🔍🔍🔍 Multi-chain verify() called 🔍🔍🔍")
        logger.info(f"  Network: {requirements.network}")
        logger.info(f"  Scheme: {requirements.scheme}")
        
        # Route based on network
        if requirements.network.startswith("solana:"):
            logger.info("  → Routing to Solana handler")
            return await self._verify_solana(payload, requirements)
        elif requirements.network.startswith("eip155:"):
            logger.info("  → Routing to EVM handler")
            return await self._verify_evm(payload, requirements)
        else:
            logger.warning(f"  ❌ Unknown network: {requirements.network}")
            return VerifyResponse(
                is_valid=False,
                invalid_reason="unsupported_network",
                invalid_message=f"Network {requirements.network} not supported",
                payer=None,
            )
    
    async def _verify_evm(
        self,
        payload: PaymentPayload,
        requirements: PaymentRequirements,
    ) -> VerifyResponse:
        """Verify EVM payment (existing logic)."""
        logger.info(f"🔍🔍🔍 EVM verify() called 🔍🔍🔍")
        logger.info(f"  payload type: {type(payload)}")
        logger.info(f"  requirements: {requirements}")
        try:
            payload_data = payload.payload
            logger.info(f"  payload.payload keys: {payload_data.keys() if isinstance(payload_data, dict) else 'not a dict'}")

            if not payload_data or "authorization" not in payload_data:
                logger.warning("Missing authorization")
                return VerifyResponse(is_valid=False, invalid_reason="missing_authorization", invalid_message="Missing authorization", payer=None)

            authorization = payload_data["authorization"]
            signature = payload_data.get("signature")
            logger.info(f"  authorization: {authorization}")
            logger.info(f"  signature present: {bool(signature)}")

            if not signature:
                logger.warning("Missing signature")
                return VerifyResponse(is_valid=False, invalid_reason="missing_signature", invalid_message="Missing signature", payer=None)

            payer = authorization.get("from")
            if not payer:
                logger.warning("Cannot extract payer")
                return VerifyResponse(is_valid=False, invalid_reason="invalid_authorization", invalid_message="Cannot extract payer", payer=None)

            for field in ["from", "to", "value", "validAfter", "validBefore", "nonce"]:
                if field not in authorization:
                    logger.warning(f"Missing field: {field}")
                    return VerifyResponse(is_valid=False, invalid_reason=f"missing_{field.lower()}", invalid_message=f"Missing {field}", payer=payer)

            if not signature.startswith("0x") or len(signature) != 132:
                logger.warning(f"Invalid signature format: {signature[:20]}...")
                return VerifyResponse(is_valid=False, invalid_reason="invalid_signature_format", invalid_message="Invalid signature format", payer=payer)

            current_time = int(time.time())
            valid_after = int(authorization["validAfter"])
            valid_before = int(authorization["validBefore"])
            logger.info(f"  time check: now={current_time}, valid_after={valid_after}, valid_before={valid_before}")

            if current_time < valid_after:
                logger.warning("Not yet valid")
                return VerifyResponse(is_valid=False, invalid_reason="valid_after_future", invalid_message="Not yet valid", payer=payer)

            if current_time > valid_before:
                logger.warning("Expired")
                return VerifyResponse(is_valid=False, invalid_reason="valid_before_expired", invalid_message="Expired", payer=payer)

            logger.info("  Verifying signature...")
            sig_valid = self._verify_eip3009_signature(authorization, signature, payer, requirements.asset)
            logger.info(f"  Signature verification result: {sig_valid}")
            if not sig_valid:
                logger.warning("Signature verification FAILED")
                return VerifyResponse(is_valid=False, invalid_reason="invalid_signature", invalid_message="Signature verification failed", payer=payer)

            logger.info("  Checking balance...")
            balance_ok = await self._check_balance(payer, requirements.asset, int(requirements.amount))
            logger.info(f"  Balance check result: {balance_ok}")
            if not balance_ok:
                logger.warning("Insufficient balance")
                return VerifyResponse(is_valid=False, invalid_reason="insufficient_balance", invalid_message="Insufficient balance", payer=payer)

            logger.info(f"✅✅✅ EVM Payment VERIFIED: {payer}, {int(requirements.amount)} ✅✅✅")
            return VerifyResponse(is_valid=True, invalid_reason=None, invalid_message=None, payer=payer)

        except Exception as e:
            logger.error(f"❌❌❌ EVM Verification EXCEPTION: {e} ❌❌❌")
            logger.error(traceback.format_exc())
            return VerifyResponse(is_valid=False, invalid_reason="verification_error", invalid_message=str(e), payer=None)
    
    async def _verify_solana(
        self,
        payload: PaymentPayload,
        requirements: PaymentRequirements,
    ) -> VerifyResponse:
        """Verify Solana payment."""
        logger.info(f"🌞🌞🌞 Solana verify() called 🌞🌞🌞")
        
        # Convert to dict format for Solana facilitator
        payload_dict = payload.model_dump() if hasattr(payload, 'model_dump') else payload
        requirements_dict = {
            "asset": requirements.asset,
            "amount": requirements.amount,
            "network": requirements.network,
        }
        
        # Call Solana facilitator
        result = self.solana_facilitator.verify_payment(payload_dict, requirements_dict)
        
        # Convert back to VerifyResponse
        return VerifyResponse(
            is_valid=result["is_valid"],
            invalid_reason=result.get("invalid_reason"),
            invalid_message=result.get("invalid_message"),
            payer=result.get("payer"),
        )
    
    async def settle(
        self,
        payload: PaymentPayload,
        requirements: PaymentRequirements,
    ) -> SettleResponse:
        """Settle payment - routes to appropriate chain handler."""
        logger.info(f"⚠️ Multi-chain settle() called")
        logger.info(f"  Network: {requirements.network}")
        
        if requirements.network.startswith("solana:"):
            return await self._settle_solana(payload, requirements)
        else:
            return await self._settle_evm(payload, requirements)
    
    async def _settle_evm(
        self,
        payload: PaymentPayload,
        requirements: PaymentRequirements,
    ) -> SettleResponse:
        """Settle EVM payment (existing logic)."""
        logger.info(f"⚠️ EVM settle() called")
        try:
            authorization = payload.payload["authorization"]
            payer = authorization.get("from", "")
            value = authorization.get("value", requirements.amount)
            logger.info(f"⚠️ EVM Settlement mocked: {payer}, {value}")
            return SettleResponse(
                success=True,
                error_reason=None,
                error_message=None,
                payer=payer,
                transaction="0x" + "00" * 32,
                network=requirements.network,
                amount=value,
            )
        except Exception as e:
            logger.error(f"EVM settlement error: {e}")
            return SettleResponse(
                success=False,
                error_reason="settlement_error",
                error_message=str(e),
                payer="",
                transaction="",
                network=requirements.network,
                amount=None,
            )
    
    async def _settle_solana(
        self,
        payload: PaymentPayload,
        requirements: PaymentRequirements,
    ) -> SettleResponse:
        """Settle Solana payment."""
        logger.info(f"🌞 Solana settle() called")
        
        payload_dict = payload.model_dump() if hasattr(payload, 'model_dump') else payload
        requirements_dict = {
            "asset": requirements.asset,
            "amount": requirements.amount,
            "network": requirements.network,
        }
        
        result = self.solana_facilitator.settle(payload_dict, requirements_dict)
        
        return SettleResponse(
            success=result["success"],
            error_reason=result.get("error_reason"),
            error_message=result.get("error_message"),
            payer=result.get("payer"),
            transaction=result.get("transaction"),
            network=result.get("network"),
            amount=result.get("amount"),
        )
    
    def _verify_eip3009_signature(
        self,
        authorization: dict[str, Any],
        signature: str,
        expected_signer: str,
        token_address: str,
    ) -> bool:
        """Verify EIP-3009 signature (EVM only)."""
        try:
            logger.info(f"  _verify_eip3009_signature: token={token_address}, signer={expected_signer}")
            from eth_account.messages import encode_typed_data

            signable = encode_typed_data(
                domain_data={"name": "USD Coin", "version": "2", "chainId": self.chain_id, "verifyingContract": Web3.to_checksum_address(token_address)},
                message_types={"TransferWithAuthorization": [{"name": "from", "type": "address"}, {"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}, {"name": "validAfter", "type": "uint256"}, {"name": "validBefore", "type": "uint256"}, {"name": "nonce", "type": "bytes32"}]},
                message_data={"from": Web3.to_checksum_address(authorization["from"]), "to": Web3.to_checksum_address(authorization["to"]), "value": int(authorization["value"]), "validAfter": int(authorization["validAfter"]), "validBefore": int(authorization["validBefore"]), "nonce": authorization["nonce"]},
            )

            recovered = Account.recover_message(signable, signature=signature)
            logger.info(f"  Recovered: {recovered}, Expected: {expected_signer}")
            result = recovered.lower() == Web3.to_checksum_address(expected_signer).lower()
            logger.info(f"  Signature valid: {result}")
            return result

        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
    
    async def _check_balance(
        self,
        payer: str,
        token_address: str,
        amount: int,
    ) -> bool:
        """Check if payer has sufficient balance (EVM only)."""
        try:
            # Simple balance check - in production would check actual balance
            # For now, assume sufficient balance for testing
            logger.info(f"  Balance check: {payer} needs {amount} of {token_address}")
            return True
        except Exception as e:
            logger.error(f"Balance check error: {e}")
            return False
