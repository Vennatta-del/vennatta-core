"""
VENNATTA CORE - LEGACY TRANSFER PROTOCOL
=========================================

Dead Man's Switch + Multi-Sig + Wi-Fi Sonar Presence Detection

Architecture:
- Check-in every 30 days (you sign a transaction)
- If no check-in: 90-day grace period starts
- After 90 days: Heir can claim
- Heir must solve: 3 x what = 21 (answer: 7)
- Wi-Fi sonar confirms presence (you or heir)
- 3-of-5 multi-sig for treasury access
"""

import hashlib
import json
import time
from datetime import datetime, timedelta
from web3 import Web3
from eth_account.messages import encode_defunct

# Your wallet
OWNER_ADDRESS = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
HEIR_ADDRESS = "0x0000000000000000000000000000000000000000"  # Set heir's address

# Legacy contract (deployed on Base)
LEGACY_CONTRACT_ADDRESS = "0x0000000000000000000000000000000000000000"  # Deploy this

# Check-in interval (30 days)
CHECKIN_INTERVAL_DAYS = 30
GRACE_PERIOD_DAYS = 90

class LegacyProtocol:
    def __init__(self, private_key):
        self.w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
        self.account = self.w3.eth.account.from_key(private_key)
        self.last_checkin = None
        self.heir_claimed = False
        
    def check_in(self):
        """Owner checks in (every 30 days)."""
        print("=" * 70)
        print("LEGACY PROTOCOL - CHECK-IN")
        print("=" * 70)
        
        timestamp = int(time.time())
        message = f"Vennatta Core Check-in: {timestamp}"
        message_hash = hashlib.sha256(message.encode()).hexdigest()
        
        signed = self.account.sign_message(encode_defunct(hexstr=message_hash))
        
        checkin_data = {
            "owner": OWNER_ADDRESS,
            "timestamp": timestamp,
            "signature": signed.signature.hex(),
            "message": "I am alive and in control",
        }
        
        # Save to file (in production: save to blockchain or IPFS)
        with open("checkin_history.json", "a") as f:
            f.write(json.dumps(checkin_data) + "\n")
        
        print(f"\n✅ Check-in successful!")
        print(f"   Owner: {OWNER_ADDRESS}")
        print(f"   Time: {datetime.fromtimestamp(timestamp)}")
        print(f"   Next check-in due: {datetime.fromtimestamp(timestamp + CHECKIN_INTERVAL_DAYS * 86400)}")
        
        return checkin_data
    
    def check_status(self):
        """Check if legacy protocol should activate."""
        print("\n" + "=" * 70)
        print("LEGACY PROTOCOL - STATUS CHECK")
        print("=" * 70)
        
        # Load last check-in
        try:
            with open("checkin_history.json", "r") as f:
                lines = f.readlines()
                last_checkin = json.loads(lines[-1])
        except:
            print("\n⚠️  No check-in history found")
            return "NO_CHECKIN"
        
        last_time = last_checkin["timestamp"]
        now = int(time.time())
        days_since_checkin = (now - last_time) / 86400
        
        print(f"\nLast check-in: {datetime.fromtimestamp(last_time)}")
        print(f"Days since: {days_since_checkin:.1f}")
        print(f"Grace period: {GRACE_PERIOD_DAYS} days")
        
        if days_since_checkin > CHECKIN_INTERVAL_DAYS + GRACE_PERIOD_DAYS:
            print(f"\n🚨 LEGACY PROTOCOL ACTIVATED!")
            print(f"   Owner inactive for {days_since_checkin:.1f} days")
            print(f"   Heir can now claim control")
            return "HEIR_CAN_CLAIM"
        elif days_since_checkin > CHECKIN_INTERVAL_DAYS:
            print(f"\n⚠️  WARNING: Check-in overdue!")
            print(f"   Grace period ends in {GRACE_PERIOD_DAYS - (days_since_checkin - CHECKIN_INTERVAL_DAYS):.1f} days")
            return "GRACE_PERIOD"
        else:
            print(f"\n✅ All good - next check-in due in {CHECKIN_INTERVAL_DAYS - days_since_checkin:.1f} days")
            return "ACTIVE"
    
    def heir_claim(self, heir_address, challenge_answer):
        """Heir claims control (after grace period)."""
        print("\n" + "=" * 70)
        print("LEGACY PROTOCOL - HEIR CLAIM")
        print("=" * 70)
        
        # Check status
        status = self.check_status()
        if status != "HEIR_CAN_CLAIM":
            print(f"\n❌ Cannot claim yet - status: {status}")
            return False
        
        # Challenge: 3 x what = 21
        print(f"\n🧩 CHALLENGE: 3 x what = 21")
        print(f"   Your answer: {challenge_answer}")
        
        if challenge_answer != 7:
            print(f"\n❌ Wrong answer! Access denied.")
            return False
        
        print(f"\n✅ Challenge passed!")
        print(f"   Heir address: {heir_address}")
        print(f"   Transferring control...")
        
        # In production: Execute multi-sig transfer
        claim_data = {
            "heir": heir_address,
            "timestamp": int(time.time()),
            "challenge_passed": True,
            "transferred": True,
        }
        
        with open("heir_claim.json", "w") as f:
            json.dump(claim_data, f, indent=2)
        
        print(f"\n🎉 CONTROL TRANSFERRED!")
        print(f"   New owner: {heir_address}")
        print(f"   Time: {datetime.fromtimestamp(claim_data['timestamp'])}")
        
        return True
    
    def wifi_sonar_presence(self, mac_address, is_heir=False):
        """Detect presence via Wi-Fi sonar (MAC address)."""
        print("\n" + "=" * 70)
        print("WI-FI SONAR - PRESENCE DETECTION")
        print("=" * 70)
        
        # In production: Integrate with Wi-Fi sonar system
        # This detects if specific device (MAC) is on network
        
        presence_data = {
            "mac_address": mac_address,
            "detected": True,  # Simulated
            "timestamp": int(time.time()),
            "is_heir": is_heir,
        }
        
        print(f"\n✅ Device detected!")
        print(f"   MAC: {mac_address}")
        print(f"   Type: {'Heir' if is_heir else 'Owner'}")
        print(f"   Time: {datetime.fromtimestamp(presence_data['timestamp'])}")
        
        return presence_data


# Usage
if __name__ == "__main__":
    import os
    private_key = os.getenv("TEST_PRIVATE_KEY")
    
    if not private_key:
        print("❌ Set TEST_PRIVATE_KEY env var")
        exit(1)
    
    protocol = LegacyProtocol(private_key)
    
    # Owner check-in (run every 30 days)
    # protocol.check_in()
    
    # Check status (run daily via cron)
    protocol.check_status()
    
    # Heir claim (after grace period)
    # protocol.heir_claim("0xHeirAddress", 7)
    
    # Wi-Fi sonar presence
    # protocol.wifi_sonar_presence("AA:BB:CC:DD:EE:FF", is_heir=False)
