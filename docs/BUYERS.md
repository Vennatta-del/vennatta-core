# Vennatta Core Buyer Guide

Vennatta Core is an x402-paid document extraction API.

## Endpoint

`POST https://vennatta-core.onrender.com/api/v1/extract-document`

## Payment flow

1. Send the JSON request.
2. Receive HTTP 402 and read `payment-required`.
3. Select the advertised Base mainnet USDC requirement.
4. Sign the payment locally using an x402 v2 buyer client.
5. Retry the same request with `PAYMENT-SIGNATURE`.
6. Read the HTTP 200 response and `PAYMENT-RESPONSE`.

Never fabricate or reuse a payment payload. Bind each payment to the live challenge.

## Example request

```json
{
  "document_text": "Your supplied text here.",
  "extraction_mode": "summary"
}
```

## Production facts

- Base mainnet: `eip155:8453`
- USDC: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- Price: `0.01 USDC`
- Payment recipient: `0x98807Ecce0D4F555d0447F79E7BdD9AA2aF0b767`
