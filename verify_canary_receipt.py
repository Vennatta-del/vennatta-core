import sqlite3
import os
import sys
from web3 import Web3

# Connect to SQLite ledger to retrieve tx_hash
conn = sqlite3.connect('gateway/gateway_ledgers.db')
cursor = conn.cursor()
cursor.execute('SELECT payment_id, tx_hash, buyer, status FROM payment_claims WHERE payment_id = "pay_e72973ad72b7d167";')
row = cursor.fetchone()
conn.close()

if not row:
    print("ERROR: Payment record not found in ledger.")
    sys.exit(1)

payment_id, tx_hash, buyer, status = row
print(f"[*] Ledger Record -> ID: {payment_id}, Status: {status}, TxHash: {tx_hash}")

if not tx_hash:
    print("ERROR: Transaction hash is missing from ledger. Downgrading to SETTLEMENT_UNKNOWN.")
    sys.exit(1)

# Dual-RPC endpoints for Base Mainnet
PRIMARY_RPC = os.environ.get("BASE_RPC_PRIMARY", "https://mainnet.base.org")
SECONDARY_RPC = os.environ.get("BASE_RPC_SECONDARY", "https://base.llamarpc.com")

def check_rpc(rpc_url):
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to RPC: {rpc_url}")
    
    chain_id = w3.eth.chain_id
    if chain_id != 8453:
        raise ValueError(f"Chain ID mismatch! Expected 8453, got {chain_id}")
        
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    if not receipt:
        raise ValueError("Transaction receipt not found (TransactionNotFound)")
        
    if receipt.status != 1:
        raise ValueError(f"Receipt status failed! Status: {receipt.status}")
        
    return w3, receipt

print("[*] Verifying via Primary RPC...")
w3_primary, receipt_primary = check_rpc(PRIMARY_RPC)

print("[*] Verifying via Secondary RPC...")
w3_secondary, receipt_secondary = check_rpc(SECONDARY_RPC)

if receipt_primary.blockNumber != receipt_secondary.blockNumber:
    print("WARNING: Block number discrepancy between primary and secondary RPCs!")

# USDC Transfer Event Signature Check: Transfer(address indexed from, address indexed to, uint256 value)
# Topic0: 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
USDC_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
EXPECTED_ASSET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913".lower()
EXPECTED_PAYTO = "0x80347776d27fA7f98e6E5703F4D2c7ffBB1977dc".lower()
EXPECTED_AMOUNT = 10000

transfer_verified = False
for log in receipt_primary.logs:
    if log['address'].lower() == EXPECTED_ASSET and len(log['topics']) >= 3:
        if log['topics'][0].hex() == USDC_TRANSFER_TOPIC:
            # Decode topics (indexed addresses are padded to 32 bytes)
            log_from = "0x" + log['topics'][1].hex()[-40:]
            log_to = "0x" + log['topics'][2].hex()[-40:]
            # Data contains the uint256 value
            log_value = int(log['data'], 16)
            
            if (log_to.lower() == EXPECTED_PAYTO and log_value == EXPECTED_AMOUNT):
                print(f"[+] Verified USDC Transfer Log found:")
                print(f"    - From: {log_from}")
                print(f"    - To: {log_to}")
                print(f"    - Value: {log_value} atomic units")
                print(f"    - Block: {receipt_primary.blockNumber}")
                print(f"    - Log Index: {log['logIndex']}")
                transfer_verified = True
                break

if not transfer_verified:
    print("ERROR: Matching USDC Transfer event log not found in receipt! Downgrading to SETTLEMENT_UNKNOWN.")
    sys.exit(1)

print("[SUCCESS] On-chain receipt verification complete. Safe to proceed with idempotency replay test.")
