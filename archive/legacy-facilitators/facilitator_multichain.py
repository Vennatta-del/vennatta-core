"""Multi-chain x402 facilitator for Vennatta Core - routes to Base, Sonic, or Solana."""

from __future__ import annotations

import logging
from typing import Any

from x402.schemas import PaymentPayload, PaymentRequirements, SettleResponse, SupportedKind, SupportedResponse, VerifyResponse
from x402.server_base import FacilitatorClient

# Import chain facilitators
from .solana_facilitator import SolanaFacilitator
from .evm_facilitator import EvmFacilitator
from .sonic_facilitator import SonicFacilitator

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("x402")
logger.setLevel(logging.DEBUG)


class VennattaFacilitator(FacilitatorClient):
    """
    Multi-chain x402 facilitator routing payments to appropriate chain facilitators.
    Supports EVM (Base), Sonic/DAG, and Solana with automatic routing based on payment network.
    """

    def __init__(self, rpc_url: str, supported_networks: list[str] | None = None, supported_schemes: list[str] | None = None):
        # Initialize chain facilitators
        self.solana_facilitator = SolanaFacilitator()
        self.evm_facilitator = EvmFacilitator(rpc_url=rpc_url)
        self.sonic_facilitator = SonicFacilitator()

        # Supported networks for all chains
        self.supported_networks = supported_networks or [
            "eip155:8453",  # Base
            "eip155:146",   # Sonic/DAG
            "solana:mainnet",  # Solana
        ]
        self.supported_schemes = supported_schemes or ["exact"]

        self.rpc_url = rpc_url

        # Route by network ID
        self.routes = {
            "eip155:8453": self.evm_facilitator,  # Base
            "eip155:1": self.evm_facilitator,     # Ethereum
            "eip155:146": self.sonic_facilitator, # Sonic/DAG
            "solana:mainnet": self.solana_facilitator,  # Solana
        }

        logger.info(f"✅ MultiChainFacilitator initialized: {len(self.routes)} chains")
        logger.info(f"   Routes: {list(self.routes.keys())}")
        logger.info(f"   🔥 3-CHAIN DOMINATION: Base, Sonic, Solana!")

    def get_supported(self) -> SupportedResponse:
        """Return supported networks from all facilitators."""
        logger.info("📞 MultiChainFacilitator.get_supported() called")
        try:
            kinds = [
                SupportedKind(network=net, scheme=scheme, x402_version=2, required_extensions=[])
                for net in self.supported_networks
                for scheme in self.supported_schemes
            ]
            response = SupportedResponse(kinds=kinds, extensions=[], signers={})
            logger.info(f"✅ get_supported() returning {len(kinds)} kinds: {kinds}")
            return response
        except Exception as e:
            logger.error(f"❌ get_supported() exception: {e}")
            raise

    async def verify(self, payload: PaymentPayload, requirements: PaymentRequirements) -> VerifyResponse:
        """Route payment verification to appropriate facilitator based on network."""
        logger.info(f"🔍 MultiChainFacilitator.verify() called for network: {requirements.network}")
        try:
            # Get the right facilitator for this network
            facilitator = self.routes.get(requirements.network)

            if not facilitator:
                logger.warning(f"Unsupported network: {requirements.network}")
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason="unsupported_network",
                    invalid_message=f"Unsupported network: {requirements.network}",
                    payer=None
                )

            # Route to appropriate facilitator
            logger.info(f"🎯 Routing to {facilitator.__class__.__name__}")
            
            # Call verify_payment on the facilitator
            result = facilitator.verify_payment(payload.dict() if hasattr(payload, 'dict') else payload, requirements.dict() if hasattr(requirements, 'dict') else requirements)
            
            # Convert dict result to VerifyResponse
            return VerifyResponse(
                is_valid=result.get("is_valid", False),
                invalid_reason=result.get("invalid_reason"),
                invalid_message=result.get("invalid_message"),
                payer=result.get("payer")
            )

        except Exception as e:
            logger.error(f"❌ verify() exception: {e}")
            return VerifyResponse(
                is_valid=False,
                invalid_reason="verification_error",
                invalid_message=str(e),
                payer=None
            )

    async def settle(self, payload: PaymentPayload, requirements: PaymentRequirements) -> SettleResponse:
        """Route payment settlement to appropriate facilitator based on network."""
        logger.info(f"⚠️ MultiChainFacilitator.settle() called for network: {requirements.network}")
        try:
            # Get the right facilitator for this network
            facilitator = self.routes.get(requirements.network)

            if not facilitator:
                logger.warning(f"Unsupported network: {requirements.network}")
                return SettleResponse(
                    success=False,
                    error_reason="unsupported_network",
                    error_message=f"Unsupported network: {requirements.network}",
                    payer="",
                    transaction="",
                    network=requirements.network,
                    amount=None
                )

            # Route to appropriate facilitator
            logger.info(f"🎯 Routing to {facilitator.__class__.__name__}")
            
            # Call settle on the facilitator
            result = facilitator.settle(payload.dict() if hasattr(payload, 'dict') else payload, requirements.dict() if hasattr(requirements, 'dict') else requirements)
            
            # Convert dict result to SettleResponse
            return SettleResponse(
                success=result.get("success", False),
                error_reason=result.get("error_reason"),
                error_message=result.get("error_message"),
                payer=result.get("payer", ""),
                transaction=result.get("transaction", ""),
                network=requirements.network,
                amount=result.get("amount")
            )

        except Exception as e:
            logger.error(f"❌ settle() exception: {e}")
            return SettleResponse(
                success=False,
                error_reason="settlement_error",
                error_message=str(e),
                payer="",
                transaction="",
                network=requirements.network,
                amount=None
            )


# Create server instance (main.py expects 'facilitator' variable)
facilitator = VennattaFacilitator
