"""Read-only Base treasury observations. No signer, retries, or settlement writes."""
import asyncio
import json
import os
import re
from decimal import Decimal
from urllib.parse import urlsplit

import httpx

TREASURY = '0x98807ecce0d4f555d0447f79e7bdd9aa2af0b767'
USDC = '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
HASH = re.compile(r'^0x[0-9a-fA-F]{64}$')


class ObservationError(Exception):
    pass


def configured_urls():
    urls = [os.getenv(name, '') for name in ('BASE_RPC_PRIMARY_URL', 'BASE_RPC_SECONDARY_URL')]
    parsed = [urlsplit(url) for url in urls]
    if any(p.scheme != 'https' or not p.hostname or p.username or p.password or p.fragment for p in parsed):
        raise ObservationError('RPC_NOT_CONFIGURED')
    if parsed[0].hostname == parsed[1].hostname:
        raise ObservationError('DISTINCT_RPC_HOSTS_REQUIRED')
    return urls


async def rpc(url, method, params):
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=False) as client:
            async with client.stream('POST', url, json={
                'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params,
            }) as response:
                response.raise_for_status()
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > 262144:
                        raise ObservationError('RPC_RESPONSE_TOO_LARGE')
                data = json.loads(body)
                if not isinstance(data, dict) or data.get('id') != 1 or 'error' in data or 'result' not in data:
                    raise ObservationError('RPC_INVALID_RESPONSE')
                return data['result']
    except (httpx.HTTPError, ValueError):
        raise ObservationError('RPC_UNAVAILABLE_OR_MALFORMED') from None


async def pair(urls, method, params):
    return await asyncio.gather(*(rpc(url, method, params) for url in urls))


async def anchor(urls):
    chains = await pair(urls, 'eth_chainId', [])
    if any(int(chain, 16) != 8453 for chain in chains):
        raise ObservationError('WRONG_CHAIN')
    tips = await pair(urls, 'eth_getBlockByNumber', ['finalized', False])
    height = min(int(block['number'], 16) for block in tips)
    blocks = await pair(urls, 'eth_getBlockByNumber', [hex(height), False])
    if any(int(block['number'], 16) != height for block in blocks):
        raise ObservationError('BLOCK_MISMATCH')
    hashes = [block['hash'].lower() for block in blocks]
    if not HASH.fullmatch(hashes[0]) or hashes[0] != hashes[1]:
        raise ObservationError('RPC_DISAGREEMENT')
    return height, hashes[0]


def amount(value, decimals):
    return format(Decimal(value) / Decimal(10 ** decimals), 'f')


def unresolved(exc):
    reason = str(exc) if isinstance(exc, ObservationError) else 'RPC_MALFORMED_RESPONSE'
    return {'status': 'SETTLEMENT_UNKNOWN', 'reason': reason, 'network': 'eip155:8453',
            'treasury': TREASURY, 'can_authorize_fulfillment': False}


async def get_treasury_snapshot():
    """Compare Base ETH/USDC balances at a shared finalized block."""
    try:
        urls = configured_urls()
        height, block_hash = await anchor(urls)
        native = [int(v, 16) for v in await pair(urls, 'eth_getBalance', [TREASURY, hex(height)])]
        call = {'to': USDC, 'data': '0x70a08231' + TREASURY[2:].zfill(64)}
        tokens = [int(v, 16) for v in await pair(urls, 'eth_call', [call, hex(height)])]
        if native[0] != native[1] or tokens[0] != tokens[1]:
            raise ObservationError('RPC_DISAGREEMENT')
        return {'status': 'corroborated', 'network': 'eip155:8453', 'treasury': TREASURY,
                'block_number': height, 'block_hash': block_hash, 'block_tag': 'finalized',
                'eth_wei': str(native[0]), 'eth': amount(native[0], 18),
                'usdc_atomic': str(tokens[0]), 'usdc': amount(tokens[0], 6),
                'sources_agree': True, 'provider_independence': 'operator_configured_not_proven'}
    except (ObservationError, ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
        return unresolved(exc)


def normalize_receipt(receipt, transaction_hash):
    if not isinstance(receipt, dict) or receipt['transactionHash'].lower() != transaction_hash.lower():
        raise ObservationError('RECEIPT_MISMATCH')
    block_hash = receipt['blockHash'].lower()
    if not HASH.fullmatch(block_hash):
        raise ObservationError('INVALID_BLOCK_HASH')
    status = int(receipt['status'], 16)
    if status not in (0, 1):
        raise ObservationError('INVALID_RECEIPT_STATUS')
    transfers = []
    for log in receipt['logs']:
        topics = log['topics']
        if log['address'].lower() != USDC or not topics or topics[0].lower() != TRANSFER:
            continue
        if len(topics) != 3 or not all(HASH.fullmatch(t) for t in topics):
            raise ObservationError('MALFORMED_TRANSFER_LOG')
        if log.get('removed') is True or log['transactionHash'].lower() != transaction_hash.lower() or log['blockHash'].lower() != block_hash:
            raise ObservationError('TRANSFER_LOG_MISMATCH')
        if not HASH.fullmatch(log['data']):
            raise ObservationError('MALFORMED_TRANSFER_AMOUNT')
        transfers.append((int(log['logIndex'], 16), topics[1].lower(), topics[2].lower(), int(log['data'], 16)))
    return {'block_number': int(receipt['blockNumber'], 16), 'block_hash': block_hash,
            'execution_status': status, 'transfers': sorted(transfers)}


async def verify_treasury_payment(transaction_hash: str):
    """Corroborate a finalized USDC receipt; not proof of customer delivery."""
    if not isinstance(transaction_hash, str) or not HASH.fullmatch(transaction_hash):
        return {'status': 'invalid_request', 'reason': 'INVALID_TRANSACTION_HASH'}
    try:
        urls = configured_urls()
        height, _ = await anchor(urls)
        raw = await pair(urls, 'eth_getTransactionReceipt', [transaction_hash])
        if any(receipt is None for receipt in raw):
            raise ObservationError('RECEIPT_NOT_FOUND_OR_UNCORROBORATED')
        receipts = [normalize_receipt(receipt, transaction_hash) for receipt in raw]
        if receipts[0] != receipts[1]:
            raise ObservationError('RPC_DISAGREEMENT')
        receipt = receipts[0]
        if receipt['block_number'] > height:
            raise ObservationError('AWAITING_FINALITY')
        blocks = await pair(urls, 'eth_getBlockByNumber', [hex(receipt['block_number']), False])
        if any(int(b['number'], 16) != receipt['block_number'] or b['hash'].lower() != receipt['block_hash'] for b in blocks):
            raise ObservationError('NONCANONICAL_OR_DISAGREEING_RECEIPT')
        incoming = [t for t in receipt['transfers'] if t[2] == '0x' + TREASURY[2:].zfill(64)]
        total = sum(t[3] for t in incoming) if receipt['execution_status'] == 1 else 0
        state = 'corroborated_payment' if total > 0 else ('transaction_failed' if receipt['execution_status'] == 0 else 'no_matching_payment')
        return {'status': state, 'transaction_hash': transaction_hash, 'network': 'eip155:8453',
                'treasury': TREASURY, 'asset': USDC, 'amount_atomic': str(total),
                'amount_usdc': amount(total, 6), 'block_number': receipt['block_number'],
                'block_hash': receipt['block_hash'], 'finalized_through': height,
                'sources_agree': True, 'delivery_verified': False, 'expected_invoice_verified': False,
                'can_authorize_fulfillment': False}
    except (ObservationError, ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
        return unresolved(exc)


def register_treasury_tools(server):
    server.tool()(get_treasury_snapshot)
    server.tool()(verify_treasury_payment)
