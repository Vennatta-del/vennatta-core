# Production Readiness Checklist (x402 Extraction Gateway)

## Architecture & Safety
- [ ] Deterministic extraction backend is default; Ollama requires explicit opt-in.
- [ ] Reviewed product results enforce source spans and no fabrication.
- [ ] Durable idempotency store (SQLite now; production DB later).
- [ ] Live facilitator calls disabled by default (`live_enabled=False`).
- [ ] Fulfillment occurs only after confirmed settlement.

## Network & Scheme Configuration
- [ ] Networks configured: Base, Base Sepolia, Polygon, Polygon Amoy, Solana, Solana Devnet.
- [ ] Schemes configured: `exact`, `upto`.
- [ ] Sonic excluded until facilitator support is confirmed.

## Facilitator Integration
- [ ] HTTP client matches official `/v2/x402/verify` and `/v2/x402/settle` shapes.
- [ ] Response fields validated: `isValid`, `success`, `transaction`, `invalidReason`, `errorReason`.
- [ ] Network and scheme mismatch fails closed.

## Testing
- [ ] Sandbox integration tests pass for Base Sepolia, Polygon Amoy, Solana Devnet.
- [ ] Replay protection verified per network.
- [ ] All tests use isolated temporary idempotency stores.

## Pre-Activation Requirements
- [ ] Official facilitator endpoint URL confirmed per network.
- [ ] API key / authentication mechanism configured.
- [ ] Real payment fixtures captured for each network/scheme.
- [ ] Settlement tested with disposable wallets on testnets.
- [ ] Idempotency store migrated to durable, atomic production DB.
- [ ] Monitoring and alerting for verification/settlement failures.
- [ ] Runbook for facilitator outage and safe fallback behavior.

## Activation Gate
- [ ] Security review completed.
- [ ] Legal / compliance sign-off for USDC micropayments.
- [ ] `live_enabled` toggled per network only after all above are satisfied.
