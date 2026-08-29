"""Treasury policy configuration with USDC-only policies and exposure limits."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional

@dataclass
class TreasuryPolicy:
    """Treasury risk management policy."""
    
    # Asset configuration
    allowed_assets: List[str] = None  # USDC-only for pilot
    max_exposure_per_day: Decimal = Decimal("1000")  # $1000 USDC daily limit
    max_exposure_per_transaction: Decimal = Decimal("100")  # $100 USDC per tx
    max_exposure_total: Decimal = Decimal("5000")  # $5000 USDC total exposure
    
    # Network configuration
    allowed_networks: List[str] = None  # Testnets only for pilot
    settlement_timeout_seconds: int = 300  # 5 minute timeout
    
    # Risk controls
    autohedge_enabled: bool = False  # Enable after 1 week stable paper performance
    paper_trading_mode: bool = True  # Start with paper trades only
    require_manual_approval_above: Optional[Decimal] = Decimal("50")  # Manual approval > $50
    
    def __post_init__(self):
        if self.allowed_assets is None:
            self.allowed_assets = ["USDC"]
        if self.allowed_networks is None:
            self.allowed_networks = ["base-sepolia", "polygon-amoy", "solana-devnet"]
    
    def is_asset_allowed(self, asset: str) -> bool:
        """Check if asset is allowed."""
        return asset.upper() in [a.upper() for a in self.allowed_assets]
    
    def is_network_allowed(self, network: str) -> bool:
        """Check if network is allowed."""
        return network.lower() in [n.lower() for n in self.allowed_networks]
    
    def check_exposure(self, amount: Decimal, current_daily: Decimal, current_total: Decimal) -> tuple[bool, str]:
        """Check if transaction would exceed exposure limits."""
        if not self.is_asset_allowed("USDC"):
            return False, "Asset not allowed"
        
        if amount > self.max_exposure_per_transaction:
            return False, f"Amount ${amount} exceeds per-transaction limit ${self.max_exposure_per_transaction}"
        
        if current_daily + amount > self.max_exposure_per_day:
            return False, f"Would exceed daily limit ${self.max_exposure_per_day}"
        
        if current_total + amount > self.max_exposure_total:
            return False, f"Would exceed total exposure limit ${self.max_exposure_total}"
        
        if self.require_manual_approval_above and amount > self.require_manual_approval_above:
            return False, f"Requires manual approval (>${self.require_manual_approval_above})"
        
        return True, "OK"

# Default pilot policy
PILOT_POLICY = TreasuryPolicy(
    allowed_assets=["USDC"],
    max_exposure_per_day=Decimal("1000"),
    max_exposure_per_transaction=Decimal("100"),
    max_exposure_total=Decimal("5000"),
    allowed_networks=["base-sepolia", "polygon-amoy", "solana-devnet"],
    paper_trading_mode=True,
    autohedge_enabled=False,
)

print("✅ TreasuryPolicy configured for USDC-only pilot")
print(f"   Daily limit: ${PILOT_POLICY.max_exposure_per_day}")
print(f"   Per-tx limit: ${PILOT_POLICY.max_exposure_per_transaction}")
print(f"   Total exposure: ${PILOT_POLICY.max_exposure_total}")
print(f"   Networks: {', '.join(PILOT_POLICY.allowed_networks)}")
print(f"   Paper trading: {PILOT_POLICY.paper_trading_mode}")
