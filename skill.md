# SKILL: Vennatta Document Extraction Gateway (x402)

## Overview
Secure, micro-payment gated document extraction gateway running on Base Mainnet via x402 protocol standards.

## Endpoints
- **GET /agent-manifest.json**: Public capability manifest and fee schedule.
- **POST /api/v1/extract-document**: Paid document extraction endpoint. Requires `PAYMENT-SIGNATURE` header containing valid Base64-encoded JSON payment proof.

## Error Codes
- `MALFORMED_OR_UNBOUND_AUTHORIZATION`: Missing nonce or malformed payment proof.
- `SETTLEMENT_VERIFICATION_ERROR`: RPC disagreement or unconfirmed transaction hash.
- `SETTLEMENT_UNKNOWN`: Transaction not found on primary or secondary RPCs.

## Limits & Pricing
- **Cost:** 10,000 atomic units (USDC) per extraction.
- **Network:** Base Mainnet (`eip155:8453`).
- **Recipient:** Configured via `RECEIVER_WALLET`.
