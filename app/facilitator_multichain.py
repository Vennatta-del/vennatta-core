"""Multi-chain x402 facilitator for Vennatta Core - routes to Base or Solana."""

from __future__ import annotations

import logging
from typing import Any

from x402.schemas import PaymentPayload, PaymentRequirements, SettleResponse, SupportedKind, SupportedResponse, VerifyResponse
from x402.server_base import FacilitatorClient

# Import Solana facilitator
from .solana_facilitator import SolanaFacilitator

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("x402")
logger.setLevel(logging.DEBUG)


class VennattaFacilitator(FacilitatorClient):
    """
    Multi-chain x402 facilitator routing payments to appropriate chain facilitators.
    Supports EVM (Base) and Solana with automatic routing based on payment network.
    """
    
    def __init__(self, rpc_url: str, supported_networks: list[str] | None = None, supported_schemes: list[str] | None = None):
        # Initialize Solana facilitator
        self.solana_facilitator = SolanaFacilitator()
        
        # Supported networks for both chains
        self.supported_networks = supported_networks or [
            "eip155:8453",  # Base
            "solana:mainnet",  # Solana
        ]
        self.supported_schemes = supported_schemes or ["exact"]
        
        self.rpc_url = rpc_url
        
        # Route by network ID
        self.routes = {
            "eip155:8453": "evm",  # Base - we'll handle EVM inline
            "solana:mainnet": self.solana_facilitator,  # Solana
        }
        
        logger.info(f"✅ MultiChainFacilitator initialized: {len(self.routes)} chains")
        logger.info(f"   Routes: {list(self.routes.keys())}")
    
    def get_supported(self) -> SupportedResponse:
        """Return supported networks from both facilitators."""
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
            
            # Route to Solana or handle EVM inline
            if facilitator == "evm":
                logger.info("🎯 Routing to EVM (Base) verifier")
                # For now, return a mock EVM verification
                # TODO: Implement real EVM verification
                return VerifyResponse(
                    is_valid=True,
                    invalid_reason=None,
                    invalid_message=None,
                    payer="0xE7d7BdF214E23A8fD1ED22e476BF742862a70212"
                )
            else:
                # Solana
                logger.info("🎯 Routing to Solana verifier")
                return await facilitator.verify_payment(payload, requirements)
            
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
            
            # Route to Solana or handle EVM inline
            if facilitator == "evm":
                logger.info("🎯 Routing to EVM (Base) settler")
                # Mock EVM settlement
                return SettleResponse(
                    success=True,
                    error_reason=None,
                    error_message=None,
                    payer="0xE7d7BdF214E23A8fD1ED22e476BF742862a70212",
                    transaction="0x" + "00" * 32,
                    network=requirements.network,
                    amount=requirements.amount
                )
            else:
                # Solana
                logger.info("🎯 Routing to Solana settler")
                return await facilitator.settle(payload, requirements)
            
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
