"""Multi-chain x402 facilitator for Vennatta Core - routes to Base or Solana."""

from __future__ import annotations

import logging
import time
import traceback
from typing import Any, Dict, Optional, Tuple

from x402.schemas import Network, PaymentPayload, PaymentRequirements, SettleResponse, SupportedKind, SupportedResponse, VerifyResponse
from x402.server_base import FacilitatorClient
from x402.payload import Payload

# Import both facilitators
from facilitator import BaseFacilitator
from facilitator_solana import SolanaFacilitator


class VennattaFacilitator(FacilitatorClient):
    """
    Multi-chain x402 facilitator routing payments to appropriate chain facilitators.
    Supports EVM (Base) and Solana with automatic routing based on payment network.
    """
    
    def __init__(self):
        # Initialize both facilitators
        self.base_facilitator = BaseFacilitator()
        self.solana_facilitator = SolanaFacilitator()
        
        # Route names
        self.routes = {
            "eip155:8453": self.base_facilitator,  # Base
            "solana:mainnet-beta": self.solana_facilitator,  # Solana
        }
    
    def get_supported(self) -> list[SupportedKind]:
        """Return supported networks from both facilitators."""
        supported = []
        
        # Add Base support
        supported.append(
            SupportedKind(
                network="eip155:8453",
                scheme="exact",
                x402Version="2",
                version="2",
            )
        )
        
        # Add Solana support
        supported.append(
            SupportedKind(
                network="solana:mainnet-beta",
                scheme="exact",
                x402Version="2",
                version="2",
            )
        )
        
        return supported
    
    def get_payment_requirements(
        self, payload: Payload, kind: SupportedKind
    ) -> PaymentRequirements:
        """Route to appropriate facilitator based on network."""
        facilitator = self.routes.get(kind.network)
        
        if not facilitator:
            raise ValueError(f"Unsupported network: {kind.network}")
        
        return facilitator.get_payment_requirements(payload, kind)
    
    async def verify_payment(
        self, payment: PaymentPayload, payload: Payload, kind: SupportedKind
    ) -> Tuple[VerifyResponse, Optional[str]]:
        """Route payment verification to appropriate facilitator."""
        facilitator = self.routes.get(kind.network)
        
        if not facilitator:
            return VerifyResponse(status="invalid"), f"Unsupported network: {kind.network}"
        
        return await facilitator.verify_payment(payment, payload, kind)
    
    async def settle_payment(
        self, payment: PaymentPayload, payload: Payload, kind: SupportedKind
    ) -> Tuple[SettleResponse, Optional[str]]:
        """Route payment settlement to appropriate facilitator."""
        facilitator = self.routes.get(kind.network)
        
        if not facilitator:
            return SettleResponse(status="invalid"), f"Unsupported network: {kind.network}"
        
        return await facilitator.settle_payment(payment, payload, kind)


# Create server instance
facilitator = VennattaFacilitator()
