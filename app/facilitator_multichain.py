"""Multi-chain x402 facilitator for Vennatta Core - routes to Base or Solana."""

from __future__ import annotations

import logging
from typing import Any

from x402.schemas import Network, PaymentPayload, PaymentRequirements, SettleResponse, SupportedKind, SupportedResponse, VerifyResponse
from x402.server_base import FacilitatorClient

# Import both facilitators
from facilitator import VennattaFacilitator as BaseFacilitator
from solana_facilitator import SolanaFacilitator

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("x402")
logger.setLevel(logging.DEBUG)


class MultiChainFacilitator(FacilitatorClient):
    """
    Multi-chain x402 facilitator routing payments to appropriate chain facilitators.
    Supports EVM (Base) and Solana with automatic routing based on payment network.
    """
    
    def __init__(self, rpc_url: str, supported_networks: list[Network] | None = None, supported_schemes: list[str] | None = None):
        # Initialize both facilitators
        self.base_facilitator = BaseFacilitator(rpc_url=rpc_url, supported_networks=supported_networks, supported_schemes=supported_schemes)
        self.solana_facilitator = SolanaFacilitator()
        
        # Supported networks for both chains
        self.supported_networks = supported_networks or [
            Network(id="eip155:8453", name="Base"),  # Base
            Network(id="solana:mainnet-beta", name="Solana"),  # Solana
        ]
        self.supported_schemes = supported_schemes or ["exact"]
        
        # Route by network ID
        self.routes = {
            "eip155:8453": self.base_facilitator,  # Base
            "solana:mainnet-beta": self.solana_facilitator,  # Solana
        }
        
        logger.info(f"✅ MultiChainFacilitator initialized: {len(self.routes)} chains")
    
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
            facilitator = self.routes.get(requirements.network.id)
            
            if not facilitator:
                logger.warning(f"Unsupported network: {requirements.network.id}")
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason="unsupported_network",
                    invalid_message=f"Unsupported network: {requirements.network.id}",
                    payer=None
                )
            
            # Route to the appropriate facilitator
            logger.info(f"🎯 Routing verify to {requirements.network.id} facilitator")
            return await facilitator.verify(payload, requirements)
            
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
        logger.info(f"⚠️ MultiChainFacilitator.settle() called for network: {requirements.network.id}")
        try:
            # Get the right facilitator for this network
            facilitator = self.routes.get(requirements.network.id)
            
            if not facilitator:
                logger.warning(f"Unsupported network: {requirements.network.id}")
                return SettleResponse(
                    success=False,
                    error_reason="unsupported_network",
                    error_message=f"Unsupported network: {requirements.network.id}",
                    payer="",
                    transaction="",
                    network=requirements.network,
                    amount=None
                )
            
            # Route to the appropriate facilitator
            logger.info(f"🎯 Routing settle to {requirements.network.id} facilitator")
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


# Create server instance
facilitator = MultiChainFacilitator
