#!/usr/bin/env python3
"""
Patch CDP SDK models to accept new x402 response format.
"""
from pathlib import Path
import re

# Find the payment requirements model file
sdk_path = Path(".venv/lib/python3.14/site-packages/cdp/openapi_client/models")

# Patch x402_payment_requirements.py to accept any scheme/network
payment_req_file = sdk_path / "x402_payment_requirements.py"
if payment_req_file.exists():
    content = payment_req_file.read_text()
    
    # Make scheme and network fields more permissive
    # Replace strict enum validation with Any
    content = re.sub(
        r"Literal\['exact', 'upto', 'batch-settlement'\]",
        "str",
        content
    )
    content = re.sub(
        r"Literal\['exact'\]",
        "str",
        content
    )
    content = re.sub(
        r"Literal\['eip155:8453', 'eip155:84532', 'eip155:137', 'eip155:42161', 'eip155:480', 'eip155:4801', 'solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp', 'solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1'\]",
        "str",
        content
    )
    content = re.sub(
        r"Literal\['base', 'base-sepolia', 'solana', 'solana-devnet'\]",
        "str",
        content
    )
    
    # Make optional fields actually optional
    content = re.sub(
        r"maxAmountRequired: str",
        "maxAmountRequired: Optional[str] = None",
        content
    )
    content = re.sub(
        r"resource: str",
        "resource: Optional[str] = None",
        content
    )
    content = re.sub(
        r"description: str",
        "description: Optional[str] = None",
        content
    )
    content = re.sub(
        r"mimeType: str",
        "mimeType: Optional[str] = None",
        content
    )
    
    # Add Optional import if not present
    if "from typing import" in content and "Optional" not in content:
        content = content.replace("from typing import", "from typing import Optional,")
    
    payment_req_file.write_text(content)
    print(f"✅ Patched {payment_req_file}")
else:
    print(f"❌ File not found: {payment_req_file}")

# Now test again
print("\nRunning test...")
import subprocess
result = subprocess.run(
    [".venv/bin/python", "scripts/cdp_x402_working.py"],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.stderr:
    print(result.stderr)
