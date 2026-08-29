"""Check CDP API URLs."""

import socket

urls = [
    "api.sandbox.cdp.coinbase.com",
    "api.cdp.coinbase.com",
    "sandbox.cdp.coinbase.com",
    "cdp.coinbase.com",
]

print("Testing CDP API domains:")
for url in urls:
    try:
        ip = socket.gethostbyname(url)
        print(f"  ✅ {url} → {ip}")
    except:
        print(f"  ❌ {url} → DNS failed")
