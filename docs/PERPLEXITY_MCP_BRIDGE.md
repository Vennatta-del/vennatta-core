# Private Perplexity MCP bridge

Status: implementation candidate, not deployed or end-to-end verified.

This runs as a separate service, leaving app.main and the paid API unchanged. It uses the official MCP Python SDK and stateless Streamable HTTP. No task submission, signing, trading, or authority updates are exposed. Gateway metadata is labeled as reported data, not independently verified execution.

## Install and test

From the repository root in a clean environment:

```sh
python -m pip install -r requirements-mcp.txt
python -m unittest discover -s tests -p 'test_mcp_bridge.py'
```

Tests are included but must be executed before release. Resolve and lock dependency versions in the tested deployment environment before production promotion.

## Configure and start

Create a dedicated random secret of at least 32 characters. Store it as VENNATTA_MCP_API_KEY in the hosting secret manager, not in GitHub or chat. Never use a wallet key as this secret.

```sh
uvicorn app.mcp_bridge:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --no-access-log
```

The SDK endpoint is /mcp. Deploy behind HTTPS on a separately approved service. Do not replace the existing gateway start command. Hosting creation and costs require separate approval. Configure the ingress to avoid logging credentials or request bodies, apply rate limits, and ensure unauthorized requests are rejected. The wrapper accepts either Authorization: Bearer <secret> or X-API-Key: <secret>, not both.

## Add to Perplexity

Account settings -> Connectors -> Custom connector -> Remote.

Name: Vennatta Private Bridge
URL: the actual deployed HTTPS service URL followed by /mcp
Transport: Streamable HTTP
Authentication: API Key

Use the actual header configuration supported by the connector UI. Confirm the header sent matches one of the server's accepted forms. Do not select None. If the UI uses a different header, update and test the adapter before exposing the service.

## Acceptance checks

1. Missing/wrong credentials return 401.
2. MCP initialize completes using an authenticated client.
3. tools/list returns the three read-only tools.
4. get_gateway_health and get_seller_capabilities return source-labeled observations or explicit unavailability.
5. get_bridge_status reports missing treasury, vault, authority, opportunity, worker and receipt integrations.
6. No paid request, transaction, task submission, or authority change occurs.
7. Perplexity successfully lists and invokes the tools.

Do not call the connector operational until these checks pass.

## Next adapters

Inspect the actual authority-manifest verification, ledger persistence, vault access and worker runtime before adding reads. Configure provider credentials independently in Vennatta's secret manager; Perplexity connector credentials are not inherited by this service. Add separately approved bounded task submission only after policy enforcement, idempotency and execution receipts are tested.
