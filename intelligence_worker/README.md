# Vennatta phase-zero node: Coinbase market access

Public Coinbase Exchange level-one BTC-USD and ETH-USD books replace the initial Kraken research adapter. No Coinbase credentials required for these public reads. This is not the authenticated Coinbase connector, a private account connection, or an execution engine. Public remains a separate connected venue in the chat, not an installed worker adapter.

Existing workflow and Render blueprint still invoke node.py and test_node.py, so they now exercise this Coinbase implementation. --once exits nonzero on invalid or failed market reads. Each book requires positive finite bid/ask prices and sizes, a timestamp no older than 30 seconds or over 5 seconds in the future, and no auction mode. Sequential snapshots are not simultaneous or executable quotes. No arbitrage, net-profit, funding or fill claims are produced.

Python 3.10+ on Linux, standard library only. Render start: python -u intelligence_worker/node.py --state /var/data/vennatta-node
Tests: python -m unittest discover -s intelligence_worker -p 'test_node.py' -v

SQLite evidence format remains compatible with phase zero. Local hash links detect inconsistent edits, not full malicious rewrites or prefix truncation without an external anchor. Startup verifies the stored chain. Single-instance lock, timeout, bounded reads, backoff, heartbeat, persistent STOP file and graceful termination remain. No event deletion, disk monitoring, external outage alerts or backup automation yet. Provision those before production acceptance.

Publishing this source does not deploy. Online GitHub validation must actually pass; then Render provider access, restart persistence and monitoring require host-level checks. Public requests from this chat's web-fetch path failed at preparation time, so no live worker test pass is claimed. Existing Coinbase connector market calls succeeded separately; they do not authenticate this process.

Private account access and trading require separately scoped Coinbase authentication and explicit execution controls. Buying Render compute does not supply Coinbase permissions. No private keys, wallet authority, minting, burning, transfers, loans, orders, revenue collection or sales are implemented. No production main or existing service changes are requested.

Provider reference: https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductbook
