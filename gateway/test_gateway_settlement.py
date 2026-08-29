import os
import sqlite3
import unittest
import tempfile
from unittest.mock import MagicMock, patch
from gateway_settlement import (
    SettlementVerifier,
    AtomicLedgerManager,
    SettlementEvidence,
    ALLOWED_TRANSITIONS,
    USDC_BASE_CONTRACT
)
from web3 import Web3
from web3.exceptions import TransactionNotFound

class TestGatewaySettlementExpanded(unittest.TestCase):
    def setUp(self):
        self.fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.ledger = AtomicLedgerManager(self.db_path)

        self.prod_db_path = os.path.expanduser("~/citadel_stack/core/gateway_ledgers.db")
        self.quarantined_payment_id = "pay_3ae7bfb64039ac55"
        self.initial_quarantine_state = self._snapshot_quarantined_record()

    def tearDown(self):
        final_quarantine_state = self._snapshot_quarantined_record()
        self.assertEqual(
            self.initial_quarantine_state,
            final_quarantine_state,
            "CRITICAL SECURITY INVADER BREACH: Quarantined production record was modified during testing!"
        )
        os.close(self.fd)
        os.remove(self.db_path)

    def _snapshot_quarantined_record(self):
        if not os.path.exists(self.prod_db_path):
            return None
        conn = sqlite3.connect(f"file:{self.prod_db_path}?mode=ro", uri=True)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM payment_claims WHERE payment_id = ?",
                (self.quarantined_payment_id,)
            )
            return cursor.fetchone()
        except sqlite3.OperationalError:
            return None
        finally:
            conn.close()

    @patch("gateway_settlement.Web3")
    def test_dual_rpc_normalized_agreement(self, mock_web3_cls):
        # Preserve static class method behavior for Web3.to_checksum_address
        mock_web3_cls.to_checksum_address.side_effect = lambda x: Web3.to_checksum_address(x)

        mock_w3_primary = MagicMock()
        mock_w3_secondary = MagicMock()
        
        mock_web3_cls.side_effect = [mock_w3_primary, mock_w3_secondary]
        mock_w3_primary.eth.chain_id = 8453
        mock_w3_secondary.eth.chain_id = 8453

        transfer_bytes = Web3.keccak(text="Transfer(address,address,uint256)")
        mock_w3_primary.keccak.return_value = transfer_bytes
        mock_w3_secondary.keccak.return_value = transfer_bytes

        verifier = SettlementVerifier("http://rpc1", "http://rpc2")

        buyer_hex = "11" * 20
        payto_hex = "22" * 20
        buyer_checksum = Web3.to_checksum_address("0x" + buyer_hex)
        payto_checksum = Web3.to_checksum_address("0x" + payto_hex)

        mock_receipt = {
            "transactionHash": "0x" + "01" * 32,
            "blockNumber": 12345,
            "blockHash": "0x" + "02" * 32,
            "status": 1,
            "logs": [{
                "address": USDC_BASE_CONTRACT,
                "topics": [
                    transfer_bytes.hex(),
                    "0x" + "00" * 12 + buyer_hex,
                    "0x" + "00" * 12 + payto_hex
                ],
                "data": "0x" + (10000).to_bytes(32, "big").hex(),
                "logIndex": 0
            }]
        }

        mock_w3_primary.eth.get_transaction_receipt.return_value = mock_receipt
        mock_w3_secondary.eth.get_transaction_receipt.return_value = mock_receipt

        mock_tx = {"to": USDC_BASE_CONTRACT, "from": buyer_checksum}
        mock_w3_primary.eth.get_transaction.return_value = mock_tx

        evidence = verifier.verify_settlement("0x" + "01" * 32, buyer_checksum, payto_checksum)
        self.assertEqual(evidence.outcome, "SETTLEMENT_CONFIRMED")
        self.assertEqual(evidence.receipt_status, 1)

    @patch("gateway_settlement.Web3")
    def test_dual_rpc_material_disagreement(self, mock_web3_cls):
        mock_w3_primary = MagicMock()
        mock_w3_secondary = MagicMock()
        
        mock_web3_cls.side_effect = [mock_w3_primary, mock_w3_secondary]
        mock_w3_primary.eth.chain_id = 8453
        mock_w3_secondary.eth.chain_id = 8453

        verifier = SettlementVerifier("http://rpc1", "http://rpc2")

        receipt_p = {
            "transactionHash": "0x" + "01" * 32,
            "blockNumber": 12345,
            "blockHash": "0x" + "02" * 32,
            "status": 1,
            "logs": []
        }
        receipt_s = {
            "transactionHash": "0x" + "01" * 32,
            "blockNumber": 99999,
            "blockHash": "0x" + "02" * 32,
            "status": 1,
            "logs": []
        }

        mock_w3_primary.eth.get_transaction_receipt.return_value = receipt_p
        mock_w3_secondary.eth.get_transaction_receipt.return_value = receipt_s

        evidence = verifier.verify_settlement("0x" + "01" * 32, "0x11"*20, "0x22"*20)
        self.assertEqual(evidence.outcome, "SETTLEMENT_UNKNOWN")
        self.assertIn("mismatch", evidence.reason)

    def test_duplicate_evidence_constraint_and_rollback(self):
        payment_id_1 = "pay_dup_1"
        payment_id_2 = "pay_dup_2"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO payment_claims (payment_id, status, updated_at) VALUES (?, ?, strftime('%s', 'now'))", (payment_id_1, "SETTLEMENT_SUBMITTED"))
            conn.execute("INSERT INTO payment_claims (payment_id, status, updated_at) VALUES (?, ?, strftime('%s', 'now'))", (payment_id_2, "SETTLEMENT_SUBMITTED"))
            conn.commit()

        evidence = SettlementEvidence(
            outcome="SETTLEMENT_CONFIRMED",
            reason="Confirmed",
            tx_hash="0xabc",
            block_number=100,
            block_hash="0xdef",
            log_index=1,
            token_contract=USDC_BASE_CONTRACT,
            sender="0x1111111111111111111111111111111111111111",
            recipient="0x2222222222222222222222222222222222222222",
            amount_atomic=10000,
            receipt_status=1
        )

        success_1 = self.ledger.atomic_update_state(payment_id_1, "SETTLEMENT_SUBMITTED", "SETTLEMENT_CONFIRMED", evidence)
        self.assertTrue(success_1)

        success_2 = self.ledger.atomic_update_state(payment_id_2, "SETTLEMENT_SUBMITTED", "SETTLEMENT_CONFIRMED", evidence)
        self.assertFalse(success_2)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM payment_claims WHERE payment_id = ?", (payment_id_2,))
            status = cursor.fetchone()[0]
            self.assertEqual(status, "SETTLEMENT_SUBMITTED")

    def test_illegal_state_transitions(self):
        payment_id = "pay_illegal_1"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO payment_claims (payment_id, status, updated_at) VALUES (?, ?, strftime('%s', 'now'))", (payment_id, "SETTLEMENT_SUBMITTED"))
            conn.commit()

        success = self.ledger.atomic_update_state(payment_id, "SETTLEMENT_SUBMITTED", "FULFILLED")
        self.assertFalse(success)

if __name__ == "__main__":
    unittest.main()
