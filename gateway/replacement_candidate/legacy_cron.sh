#!/bin/bash
# Daily legacy protocol check (add to crontab)
# Runs every day at 9 AM

cd ~/vennatta_core
source .venv/bin/activate
export TEST_PRIVATE_KEY="7de71eea10233882731dc82d3b1259f5483913ddb2e52e670bcbe59c697f0cfe"

python3 -c "
from legacy_protocol import LegacyProtocol
import os

protocol = LegacyProtocol(os.getenv('TEST_PRIVATE_KEY'))
status = protocol.check_status()

if status == 'GRACE_PERIOD' or status == 'HEIR_CAN_CLAIM':
    # Send alert (email, SMS, etc.)
    print('🚨 LEGACY ALERT: Check status!')
"
