from x402.schemes.x402 import X402Scheme
from x402.facilitator_base import (
    FacilitatorServer,
    SupportedKind,
    FacilitatorConfig,
    PaymentRequirements,
    X402Payment,
    PaymentStatus,
    PaymentState,
)
from x402.http.x402_http_server_base import X402HttpServerConfig
from x402.payload import Payload
from typing import Dict, Optional, Tuple
from decimal import Decimal
import time
import secrets

# Import both facilitators
from facilitator import BaseFacilitator
from facilitator_solana import SolanaFacilitator


class VennattaFacilitator(FacilitatorServer):
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
        
        # Initialize base facilitator (it has the routes)
        self.base_facilitator.initialize()
    
    def get_supported(self) -> list[SupportedKind]:
        """Return supported networks from both facilitators."""
        supported = []
        
        # Add Base support
        supported.append(
            SupportedKind(
                network="eip155:8453",
                scheme="exact",
                x402Version="2",  # Add this field!
                version="2",
            )
        )
        
        # Add Solana support
        supported.append(
            SupportedKind(
                network="solana:mainnet-beta",
                scheme="exact",
                x402Version="2",  # Add this field!
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
        self, payment: X402Payment, payload: Payload, kind: SupportedKind
    ) -> Tuple[PaymentStatus, Optional[str]]:
        """Route payment verification to appropriate facilitator."""
        facilitator = self.routes.get(kind.network)
        
        if not facilitator:
            return PaymentStatus.INVALID, f"Unsupported network: {kind.network}"
        
        return await facilitator.verify_payment(payment, payload, kind)
    
    async def settle_payment(
        self, payment: X402Payment, payload: Payload, kind: SupportedKind
    ) -> Tuple[PaymentStatus, Optional[str]]:
        """Route payment settlement to appropriate facilitator."""
        facilitator = self.routes.get(kind.network)
        
        if not facilitator:
            return PaymentStatus.INVALID, f"Unsupported network: {kind.network}"
        
        return await facilitator.settle_payment(payment, payload, kind)


# Create server instance
facilitator = VennattaFacilitator()
