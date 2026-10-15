import copy
import unittest
from unittest.mock import patch

from app import treasury_reads as t

TX = '0x' + '1' * 64
BLOCK = '0x' + '2' * 64
ENV = {'BASE_RPC_PRIMARY_URL': 'https://one.example/rpc',
       'BASE_RPC_SECONDARY_URL': 'https://two.example/rpc'}


class TreasuryTests(unittest.IsolatedAsyncioTestCase):
    def receipt(self):
        return {'transactionHash': TX, 'blockHash': BLOCK, 'blockNumber': '0x5',
                'status': '0x1', 'logs': [{'address': t.USDC,
                'topics': [t.TRANSFER, '0x' + '0' * 24 + '3' * 40,
                           '0x' + t.TREASURY[2:].zfill(64)],
                'data': '0x' + format(10000, '064x'), 'logIndex': '0x0',
                'transactionHash': TX, 'blockHash': BLOCK, 'removed': False}]}

    async def fake_rpc(self, url, method, params):
        if method == 'eth_chainId':
            return '0x2105'
        if method == 'eth_getBlockByNumber':
            return {'number': '0xa' if params[0] == 'finalized' else params[0], 'hash': BLOCK}
        if method == 'eth_getBalance':
            return '0x0'
        if method == 'eth_call':
            return '0x2710'
        if method == 'eth_getTransactionReceipt':
            return self.receipt()
        raise AssertionError(method)

    async def test_snapshot(self):
        with patch.dict('os.environ', ENV, clear=True), patch.object(t, 'rpc', side_effect=self.fake_rpc):
            result = await t.get_treasury_snapshot()
        self.assertEqual(result['status'], 'corroborated')
        self.assertEqual(result['usdc'], '0.01')

    async def test_payment(self):
        with patch.dict('os.environ', ENV, clear=True), patch.object(t, 'rpc', side_effect=self.fake_rpc):
            result = await t.verify_treasury_payment(TX)
        self.assertEqual(result['status'], 'corroborated_payment')
        self.assertEqual(result['amount_usdc'], '0.01')
        self.assertFalse(result['can_authorize_fulfillment'])

    async def test_missing_config(self):
        with patch.dict('os.environ', {}, clear=True):
            result = await t.get_treasury_snapshot()
        self.assertEqual(result['status'], 'SETTLEMENT_UNKNOWN')

    async def test_rpc_failure(self):
        with patch.dict('os.environ', ENV, clear=True), patch.object(t, 'rpc', side_effect=t.ObservationError('RPC_UNAVAILABLE_OR_MALFORMED')):
            result = await t.verify_treasury_payment(TX)
        self.assertEqual(result['status'], 'SETTLEMENT_UNKNOWN')

    async def test_wrong_chain(self):
        async def wrong(url, method, params):
            return '0x1' if method == 'eth_chainId' else await self.fake_rpc(url, method, params)
        with patch.dict('os.environ', ENV, clear=True), patch.object(t, 'rpc', side_effect=wrong):
            result = await t.get_treasury_snapshot()
        self.assertEqual(result['reason'], 'WRONG_CHAIN')

    async def test_balance_disagreement(self):
        async def disagree(url, method, params):
            if method == 'eth_call' and 'two.example' in url:
                return '0x0'
            return await self.fake_rpc(url, method, params)
        with patch.dict('os.environ', ENV, clear=True), patch.object(t, 'rpc', side_effect=disagree):
            result = await t.get_treasury_snapshot()
        self.assertEqual(result['reason'], 'RPC_DISAGREEMENT')

    async def test_receipt_disagreement(self):
        async def disagree(url, method, params):
            result = await self.fake_rpc(url, method, params)
            if method == 'eth_getTransactionReceipt' and 'two.example' in url:
                result = copy.deepcopy(result)
                result['status'] = '0x0'
            return result
        with patch.dict('os.environ', ENV, clear=True), patch.object(t, 'rpc', side_effect=disagree):
            result = await t.verify_treasury_payment(TX)
        self.assertEqual(result['reason'], 'RPC_DISAGREEMENT')

    async def test_failed_transaction(self):
        async def failed(url, method, params):
            result = await self.fake_rpc(url, method, params)
            if method == 'eth_getTransactionReceipt':
                result['status'] = '0x0'
                result['logs'] = []
            return result
        with patch.dict('os.environ', ENV, clear=True), patch.object(t, 'rpc', side_effect=failed):
            result = await t.verify_treasury_payment(TX)
        self.assertEqual(result['status'], 'transaction_failed')

    async def test_unfinalized(self):
        async def pending(url, method, params):
            result = await self.fake_rpc(url, method, params)
            if method == 'eth_getTransactionReceipt':
                result['blockNumber'] = '0xb'
            return result
        with patch.dict('os.environ', ENV, clear=True), patch.object(t, 'rpc', side_effect=pending):
            result = await t.verify_treasury_payment(TX)
        self.assertEqual(result['reason'], 'AWAITING_FINALITY')

    async def test_invalid_hash(self):
        self.assertEqual((await t.verify_treasury_payment('bad'))['status'], 'invalid_request')


if __name__ == '__main__':
    unittest.main()
