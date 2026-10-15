"""Vennatta phase-zero node: read-only research and durable evidence. No executor."""
import argparse, fcntl, hashlib, json, os, signal, sqlite3, threading, time, urllib.request, uuid
from decimal import Decimal
from pathlib import Path

URL = "https://api.kraken.com/0/public/Ticker?pair=ETHUSD,XBTUSD,ETHXBT"
STOP = threading.Event()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)

class Ledger:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=10, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS evidence(seq INTEGER PRIMARY KEY,event_id TEXT UNIQUE,at REAL,kind TEXT,body TEXT,previous TEXT,digest TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS heartbeat(id INTEGER PRIMARY KEY CHECK(id=1),at REAL,status TEXT)")

    def append(self, kind, body):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT digest FROM evidence ORDER BY seq DESC LIMIT 1").fetchone()
            previous = row[0] if row else "0" * 64
            event = {"event_id":str(uuid.uuid4()),"at":time.time(),"kind":kind,"body":body,"previous":previous}
            digest = hashlib.sha256(canonical(event).encode()).hexdigest()
            self.db.execute("INSERT INTO evidence(event_id,at,kind,body,previous,digest) VALUES(?,?,?,?,?,?)",(event["event_id"],event["at"],kind,canonical(body),previous,digest))
            self.db.execute("INSERT INTO heartbeat VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET at=excluded.at,status=excluded.status",(event["at"],kind))
            self.db.execute("COMMIT")
            return digest
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def verify(self):
        previous = "0" * 64
        for event_id, at, kind, body, parent, digest in self.db.execute("SELECT event_id,at,kind,body,previous,digest FROM evidence ORDER BY seq"):
            event = {"event_id":event_id,"at":at,"kind":kind,"body":json.loads(body),"previous":parent}
            if parent != previous or hashlib.sha256(canonical(event).encode()).hexdigest() != digest:
                return False
            previous = digest
        return True

    def close(self):
        self.db.close()

def assess(data):
    if data.get("error"):
        raise ValueError("provider_error")
    quotes = []
    for key in ("XETHZUSD", "XXBTZUSD", "XETHXXBT"):
        item = data["result"][key]
        bid, ask = Decimal(item["b"][0]), Decimal(item["a"][0])
        if not all(x.is_finite() and x > 0 for x in (bid,ask)) or bid > ask:
            raise ValueError("invalid_quote")
        quotes.append((bid,ask))
    (eb,ea),(bb,ba),(xb,xa) = quotes
    factors = (xb*bb/ea, eb/(ba*xa))
    return {"source":URL,"gross_routes":[{"route":route,"fraction":str(factor-1),"executable":False} for route,factor in zip(("USD_ETH_BTC_USD","USD_BTC_ETH_USD"),factors)],"status":"costs_depth_funding_and_execution_unverified","revenue_verified":False}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise ValueError("redirect_rejected")

def fetch():
    request = urllib.request.Request(URL,headers={"User-Agent":"VennattaResearch/0.3","Accept":"application/json"})
    with urllib.request.build_opener(NoRedirect()).open(request,timeout=10) as response:
        if response.status != 200:
            raise ValueError("unexpected_http_status")
        body = response.read(262145)
    if len(body) > 262144:
        raise ValueError("response_too_large")
    return json.loads(body)

def cycle(ledger, fetcher=fetch):
    started = time.monotonic()
    try:
        report = assess(fetcher())
        if time.monotonic()-started > 15:
            raise ValueError("slow_observation")
        kind = "OBSERVATION"
    except Exception as exc:
        kind, report = "ERROR", {"reason_type":type(exc).__name__,"revenue_verified":False}
    digest = ledger.append(kind,report)
    print(canonical({"event":kind,"digest":digest,"report":report}),flush=True)
    return kind == "OBSERVATION"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state",default="state")
    parser.add_argument("--once",action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    state = Path(args.state)
    state.mkdir(parents=True,exist_ok=True)
    lock = (state/"node.lock").open("a")
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    ledger = Ledger(state/"evidence.sqlite3")
    if not ledger.verify():
        ledger.close()
        raise RuntimeError("Evidence verification failed; refusing to append")
    for sig in (signal.SIGTERM,signal.SIGINT):
        signal.signal(sig,lambda *_:STOP.set())
    failures = 0
    try:
        while not STOP.is_set():
            if (state/"STOP").exists():
                ledger.append("STOPPED",{"reason":"persistent_kill_switch"})
                break
            okay = cycle(ledger)
            failures = 0 if okay else min(failures+1,6)
            if args.once:
                return 0 if okay else 1
            STOP.wait(min(3600,60*2**failures))
    finally:
        ledger.close()
        lock.close()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
