# x402 payment checkpoint

Date: 2026-09-14

## Working configuration

- Seller: `127.0.0.1:8000`
- Network: `eip155:8453`
- Asset: Base USDC
- Amount: `10000` atomic units (`0.01 USDC`)
- Treasury: `0x98807Ecce0D4F555d0447F79E7BdD9AA2aF0b767`
- Buyer: `0x16864a8d99A66F3e9D3230FB9256753E7Fa640B4`

## Successful result

- Seller returned `402 Payment Required` before payment.
- x402 HTTPX buyer completed the payment-enabled retry.
- CDP verification completed successfully.
- CDP settlement completed successfully.
- Seller returned HTTP 200 with the protected response.
- Payment response header was received.

## Safety

Do not rerun the buyer script unless another 0.01 USDC payment is intended.
Do not commit private keys, CDP secrets, or environment files.
