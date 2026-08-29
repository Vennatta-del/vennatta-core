import os
import json
import sqlite3
import logging
from dataclasses import dataclass, field
from typing import Literal, Optional, Dict, Any, Tuple
from web3 import Web3
from web3.types import TxReceipt
from web3.exceptions import TransactionNotFound

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("GatewaySettlementEngine")

USDC_BASE_CONTRACT = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
BASE_CHAIN_ID = 8453
EXPECTED_AMOUNT_ATOMIC = 10000

# Strict state transition map
ALLOWED_TRANSITIONS = {
    "SETTLEMENT_SUBMITTED": {"SETTLEMENT_CONFIRMED", "SETTLEMENT_UNKNOWN", "SETTLEMENT_FAILED"},
    "SETTLEMENT_UNKNOWN": {"SETTLEMENT_CONFIRMED", "SETTLEMENT_FAILED"},
    "SETTLEMENT_CONFIRMED": {"PROCESSING"},
    "PROCESSING": {"RESULT_PERSISTED", "PROCESSING_FAILED"},
    "RESULT_PERSISTED": {"FULFILLED"},
}

@dataclass
class SettlementEvidence:
    outcome: Literal["SETTLEMENT_CONFIRMED", "SETTLEMENT_UNKNOWN", "SETTLEMENT_FAILED"]
    reason: str
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    log_index: Optional[int] = None
    confirmations: Optional[int] = None
    token_contract: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    amount_atomic: Optional[int] = None
    receipt_status: Optional[int] = None

def normalize_hex(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "hex"):
        return value.hex()
    return str(value)

def decode_uint256(data: Any) -> int:
    if isinstance(data, (bytes, bytearray)):
        if len(data) != 32:
            raise ValueError(f"Expected 32 bytes for uint256 data, got {len(data)}")
        return int.from_bytes(data, "big")
    if hasattr(data, "hex") and not isinstance(data, str):
        b = data.hex()
        if len(b) != 64:
            raise ValueError(f"Expected 32-byte hex for uint256 data, got {len(b)} chars")
        return int(b, 16)
    if isinstance(data, str):
        clean_str = data[2:] if data.startswith("0x") else data
        if len(clean_str) != 64:
            raise ValueError(f"Expected 64 hex chars for uint256 data, got {len(clean_str)}")
        return int(clean_str, 16)
    raise ValueError("Unsupported log data type for uint256 decoding")

def normalize_logs(receipt: TxReceipt) -> Tuple[Dict[str, Any], ...]:
    rows = []
    for log in receipt.get("logs", []):
        addr = normalize_hex(log.get("address"))
        rows.append({
            "address": addr.lower() if addr else "",
            "topics": tuple(normalize_hex(t).lower() for t in log.get("topics", [])),
            "data": normalize_hex(log.get("data", "0x")).lower(),
            "log_index": int(log.get("logIndex", 0)),
        })
    return tuple(sorted(rows, key=lambda x: x["log_index"]))

class SettlementVerifier:
    def __init__(self, primary_rpc_url: str, secondary_rpc_url: str):
        self.w3_primary = Web3(Web3.HTTPProvider(primary_rpc_url))
        self.w3_secondary = Web3(Web3.HTTPProvider(secondary_rpc_url))

    def _normalize_receipt_headers(self, receipt: TxReceipt) -> Dict[str, Any]:
        return {
            "tx_hash": normalize_hex(receipt.get("transactionHash")),
            "block_number": int(receipt.get("blockNumber", 0)),
            "block_hash": normalize_hex(receipt.get("blockHash")),
            "status": int(receipt.get("status", 0)),
            "logs": normalize_logs(receipt),
        }

    def verify_settlement(self, tx_hash: str, expected_buyer: str, expected_payto: str) -> SettlementEvidence:
        try:
            p_chain = self.w3_primary.eth.chain_id
            s_chain = self.w3_secondary.eth.chain_id
            if p_chain != BASE_CHAIN_ID or s_chain != BASE_CHAIN_ID:
                return SettlementEvidence(
                    "SETTLEMENT_FAILED",
                    "RPC provider chain ID mismatch with Base mainnet (8453)",
                    receipt_status=None
                )
        except Exception:
            return SettlementEvidence("SETTLEMENT_UNKNOWN", "Failed to retrieve chain IDs from RPCs", receipt_status=None)

        try:
            p_receipt = self.w3_primary.eth.get_transaction_receipt(tx_hash)
        except TransactionNotFound:
            return SettlementEvidence("SETTLEMENT_UNKNOWN", "Transaction or receipt not found on primary RPC", receipt_status=None)
        except Exception:
            return SettlementEvidence("SETTLEMENT_UNKNOWN", "Primary RPC provider failure during receipt fetch", receipt_status=None)

        try:
            s_receipt = self.w3_secondary.eth.get_transaction_receipt(tx_hash)
        except TransactionNotFound:
            return SettlementEvidence("SETTLEMENT_UNKNOWN", "Transaction or receipt not found on secondary RPC", receipt_status=None)
        except Exception:
            return SettlementEvidence("SETTLEMENT_UNKNOWN", "Secondary RPC provider failure during receipt fetch", receipt_status=None)

        if not p_receipt or not s_receipt:
            return SettlementEvidence("SETTLEMENT_UNKNOWN", "Receipt missing on one or more providers", receipt_status=None)

        norm_p = self._normalize_receipt_headers(p_receipt)
        norm_s = self._normalize_receipt_headers(s_receipt)

        if norm_p != norm_s:
            logger.error("Dual-RPC disagreement detected on normalized receipt data or logs.")
            return SettlementEvidence("SETTLEMENT_UNKNOWN", "Primary and secondary RPC receipt/log normalization mismatch", receipt_status=None)

        try:
            tx_obj = self.w3_primary.eth.get_transaction(tx_hash)
            tx_to = normalize_hex(tx_obj.get("to"))
            if not tx_to or tx_to.lower() != USDC_BASE_CONTRACT.lower():
                return SettlementEvidence("SETTLEMENT_FAILED", "Transaction destination does not match canonical USDC contract", receipt_status=0)
        except Exception:
            return SettlementEvidence("SETTLEMENT_UNKNOWN", "Failed to fetch parent transaction details for binding validation", receipt_status=None)

        if norm_p["status"] != 1:
            return SettlementEvidence("SETTLEMENT_FAILED", f"Transaction execution reverted with status {norm_p['status']}", receipt_status=0)

        expected_topic0 = normalize_hex(
            self.w3_primary.keccak(text="Transfer(address,address,uint256)")
        ).lower()

        valid_transfer_found = False
        matched_log = None

        for log in p_receipt.get("logs", []):
            addr = normalize_hex(log.get("address"))
            if not addr or addr.lower() != USDC_BASE_CONTRACT.lower():
                continue
            topics = log.get("topics", [])
            if len(topics) < 3:
                continue

            topic0 = normalize_hex(topics[0]).lower()
            if topic0 != expected_topic0:
                continue

            try:
                sender = Web3.to_checksum_address("0x" + normalize_hex(topics[1])[-40:])
                recipient = Web3.to_checksum_address("0x" + normalize_hex(topics[2])[-40:])
                amount = decode_uint256(log.get("data"))
            except Exception:
                continue

            if (
                sender.lower() == expected_buyer.lower() and
                recipient.lower() == expected_payto.lower() and
                amount == EXPECTED_AMOUNT_ATOMIC
            ):
                valid_transfer_found = True
                matched_log = {
                    "log_index": int(log.get("logIndex", 0)),
                    "token_contract": USDC_BASE_CONTRACT,
                    "sender": sender,
                    "recipient": recipient,
                    "amount": amount
                }
                break

        if not valid_transfer_found or not matched_log:
            return SettlementEvidence("SETTLEMENT_FAILED", "No matching canonical USDC Transfer event found matching criteria", receipt_status=1)

        return SettlementEvidence(
            outcome="SETTLEMENT_CONFIRMED",
            reason="Successfully verified matching Base mainnet receipt, transaction binding, and canonical USDC transfer.",
            tx_hash=norm_p["tx_hash"],
            block_number=norm_p["block_number"],
            block_hash=norm_p["block_hash"],
            log_index=matched_log["log_index"],
            token_contract=matched_log["token_contract"],
            sender=matched_log["sender"],
            recipient=matched_log["recipient"],
            amount_atomic=matched_log["amount"],
            receipt_status=1
        )

class AtomicLedgerManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS payment_claims (
                    payment_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settlements (
                    payment_id TEXT PRIMARY KEY,
                    tx_hash TEXT NOT NULL,
                    block_number INTEGER,
                    block_hash TEXT,
                    receipt_status INTEGER,
                    token_contract TEXT,
                    sender TEXT,
                    recipient TEXT,
                    amount_atomic INTEGER,
                    log_index INTEGER,
                    chain_status TEXT,
                    confirmed_at INTEGER,
                    FOREIGN KEY(payment_id) REFERENCES payment_claims(payment_id)
                );
            """)
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_settlement_log 
                ON settlements(tx_hash, log_index, token_contract);
            """)
            conn.commit()

    def atomic_update_state(self, payment_id: str, expected_old_status: str, new_status: str, evidence: Optional[SettlementEvidence] = None) -> bool:
        allowed_next = ALLOWED_TRANSITIONS.get(expected_old_status, set())
        if new_status not in allowed_next:
            logger.error(f"Illegal state transition requested: {expected_old_status} -> {new_status}")
            return False

        conn = sqlite3.connect(self.db_path, timeout=5.0, isolation_level=None)
        try:
            conn.execute("PRAGMA busy_timeout = 5000;")
            conn.execute("BEGIN IMMEDIATE;")
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE payment_claims 
                SET status = ?, updated_at = strftime('%s', 'now')
                WHERE payment_id = ? AND status = ?
            """, (new_status, payment_id, expected_old_status))

            if cursor.rowcount != 1:
                conn.execute("ROLLBACK;")
                logger.warning(f"Compare-and-set conflict or missing record for payment_id {payment_id} (expected old status: {expected_old_status})")
                return False

            if evidence and evidence.outcome in ("SETTLEMENT_CONFIRMED", "SETTLEMENT_FAILED"):
                cursor.execute("""
                    INSERT INTO settlements (
                        payment_id, tx_hash, block_number, block_hash, receipt_status,
                        token_contract, sender, recipient, amount_atomic, log_index, chain_status, confirmed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%s', 'now'))
                """, (
                    payment_id, evidence.tx_hash, evidence.block_number, evidence.block_hash,
                    evidence.receipt_status, evidence.token_contract, evidence.sender, evidence.recipient,
                    evidence.amount_atomic, evidence.log_index, evidence.outcome
                ))

            conn.commit()
            return True
        except sqlite3.IntegrityError as ie:
            conn.execute("ROLLBACK;")
            logger.error(f"Database integrity constraint violation: {ie}")
            return False
        except Exception as e:
            conn.execute("ROLLBACK;")
            logger.error(f"Atomic transaction aborted due to error: {e}")
            raise
        finally:
            conn.close()
