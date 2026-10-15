# Vennatta autonomous financial node: phase zero

Read-only crypto observations plus a shared evidence-ledger foundation. NOT a deployed worker, autonomous reasoning engine, trader, facilitator, salesperson, or proven revenue system.

## Runtime
Python 3.10+ on Linux; standard library only. Build: python -m unittest discover -s intelligence_worker -p 'test_node.py' -v
Start: python -u intelligence_worker/node.py --state /var/data/vennatta-node
A dedicated Render worker and persistent disk are described by render-financial-intelligence.yaml. No existing service or production main configuration is changed. No wallet keys, mint authority, private account data or paid AI APIs are needed. No port is served.

## Evidence and recovery
SQLite WAL persists events, UUIDs, timestamps, hash links, and heartbeat. Startup checks existing chain consistency. The process has a single-instance lock, bounded reads, timeout, retry backoff and graceful termination. A STOP file in the state directory prevents future cycles. Events are not automatically deleted: provision monitoring, backups and archival before the disk fills. Independent outage notification is not yet implemented.

This local hash chain detects inconsistent edits, not a malicious complete rewrite or valid-prefix truncation without an external checkpoint. It is NOT immutable, externally anchored, or proof of payment. The current writer emits observations, errors and stop events only. Proposal/approval/submission/receipt/reconciliation schemas and authorized executors are future work; this code does not claim those controls are implemented.

## Market limits
Public Kraken ETHUSD, XBTUSD and ETHXBT ticker quotes produce two gross triangular-route observations. Fees, depth, slippage, capital and execution timing remain unverified. Exchange timestamps are unavailable here. No output is an executable trade or realized profit. Unknown costs are not treated as zero. Provider access and expected pair identifiers must be verified on the actual host. Tests use fixtures, not live market requests.

## Deployment acceptance
Source publication does not deploy anything. Require passed build tests, actual OBSERVATION logs, provider failure handling, persistence across restart, and a monitoring/backup plan before production acceptance. Repeated ERROR events mean the research is not working, even if the process is live. Render connector lacks worker-creation/disk-attachment operations at preparation time; do not substitute an unrelated web service. Review actual charges before activation. No automatic deployments are requested.

## Authority
No signing, minting, burning, transfers, borrowing, leverage, publishing or accepting jobs. Future permission changes must be explicit and tested; process restarts must reconcile existing external transactions instead of resubmitting blindly.
