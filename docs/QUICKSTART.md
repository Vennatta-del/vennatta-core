# Vennatta Core - Quickstart Guide

## What is Vennatta Core?

Vennatta Core is a **multi-chain x402 payment facilitator** that enables AI agents and APIs to accept crypto payments natively over HTTP.

**Supported chains:**
- ⚡ Base (eip155:8453)
- ⚡ Sonic/DAG (eip155:146)
- 🌞 Solana (solana:mainnet)

## How It Works

1. Client sends HTTP request with x402 payment payload
2. Vennatta Core cryptographically verifies the payment
3. If valid, request is processed
4. Treasury receives 90% of payment (you keep 10% for ops)

## Quick Integration (3 lines)

### Python Example

```python
import requests
from eth_account import Account
from eth_account.messages import encode_defunct

# 1. Sign payment message
private_key = "YOUR_PRIVATE_KEY"
message = "Pay 10000 USDC to 0xTREASURY on eip155:8453"
signature = Account.sign_message(encode_defunct(text=message), private_key)

# 2. Create payment headers
headers = {
    "X-Payment-Network": "eip155:8453",
    "X-Payment-Scheme": "exact",
    "X-Payment-Price": "10000 USDC",
    "X-Payment-Pay-To": "0xTREASURY",
    "X-Payment-Payload": json.dumps({
        "payload": {
            "authorization": {"payer": Account.from_key(private_key).address},
            "signature": f"0x{signature.signature.hex()}"
        }
    })
}

# 3. Send request
response = requests.post(
    "[https://vennatta-core.onrender.com/api/v1/extract-document](https://vennatta-core.onrender.com/api/v1/extract-document)",
    json={"your": "data"},
    headers=headers
)
print(response.json())
```

### cURL Example

```bash
curl -X POST [https://vennatta-core.onrender.com/api/v1/extract-document](https://vennatta-core.onrender.com/api/v1/extract-document) \
  -H "Content-Type: application/json" \
  -H "X-Payment-Network: eip155:8453" \
  -H "X-Payment-Scheme: exact" \
  -H "X-Payment-Price: 10000 USDC" \
  -H "X-Payment-Pay-To: 0xTREASURY" \
  -H "X-Payment-Payload: {\"payload\":{\"authorization\":{\"payer\":\"0xYOUR_ADDRESS\"},\"signature\":\"0xSIGNATURE\"}}" \
  -d '{"your": "data"}'
```

## Payment Payload Format

```json
{
  "payload": {
    "authorization": {
      "payer": "0xYOUR_ADDRESS",
      "from": "0xYOUR_ADDRESS"
    },
    "signature": "0xSIGNATURE"
  }
}
```

## Supported Networks

| Network | Chain ID | RPC URL |
|---------|----------|---------|
| Base | eip155:8453 | https://mainnet.base.org |
| Sonic/DAG | eip155:146 | https://rpc.soniclabs.com |
| Solana | solana:mainnet | https://api.mainnet-beta.solana.com |

## Pricing

- **Default:** 0.01 USDC per request
- **Treasury split:** 90% to treasury, 10% for ops
- **Custom pricing:** Contact us

## API Endpoints

- `POST /api/v1/extract-document` - Extract structured data from documents
- `POST /api/v1/extract-obsidian` - Extract from Obsidian vaults
- `GET /health` - Health check

## Need Help?

- GitHub: [Vennatta Core](https://github.com/Vennatta-del/vennatta-core)
- Docs: [Full API Reference](./API_REFERENCE.md)

---

**Built with 🔥 by Vennatta - Powering the $1T/month autonomous AI economy**
