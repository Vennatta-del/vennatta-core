import os
import sys
import json
import time
from x402_buyer_client import X402Buyer, PolicyValidator, ProductionSigner

def enforce_safety_gates():
    if os.getenv("X402_LIVE_CONFIRM") != "I_UNDERSTAND_ONE_REAL_PAYMENT":
        raise RuntimeError("CRITICAL: Live mode not explicitly enabled.")
    if int(os.getenv("MAX_CALLS", "1")) != 1:
        raise RuntimeError("CRITICAL: MAX_CALLS must be exactly 1.")
    if int(os.getenv("MAX_SPEND_ATOMIC", "10000")) != 10000:
        raise RuntimeError("CRITICAL: Spend cap mismatch.")

def main():
    try:
        enforce_safety_gates()
    except Exception as e:
        print(f"[ABORT] {e}")
        sys.exit(1)

    resource = os.getenv("ALLOWED_RESOURCE", "https://agentcitadel.dev/api/v1/extract-document")
    expected_payto = os.getenv("EXPECTED_PAYTO", "0x80347776d27fA7f98e6E5703F4D2c7ffBB1977dc")
    private_key = os.getenv("ETH_PRIVATE_KEY")
    buyer_address = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"

    if not private_key:
        print("[FATAL] ETH_PRIVATE_KEY is required.")
        sys.exit(1)

    policy = PolicyValidator(
        expected_resource=resource,
        expected_network="eip155:8453",
        expected_asset="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        expected_amount="10000",
        expected_payto=expected_payto
    )

    signer = ProductionSigner(private_key, buyer_address)
    buyer = X402Buyer(policy=policy, signer=signer)

    print("\n=== STARTING ONE-SHOT PRODUCTION SMOKE TEST ===")
    start_time = time.time()

    try:
        payload = {"content": "Vennatta one-shot production smoke test payload"}
        response = buyer.call(resource, payload)
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        print("\n=== SMOKE TEST SUCCESSFUL ===")
        print(f"Result: {json.dumps(response, indent=2)}")
        print(f"Elapsed Time: {elapsed_ms} ms")

    except Exception as e:
        print(f"\n[FATAL ERROR] Smoke test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
