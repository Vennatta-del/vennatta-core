"""Coinbase public market observations; no private account access or execution."""
import argparse, fcntl, hashlib, json, os, signal, sqlite3, threading, time, urllib.request, uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path

PRODUCTS = ("BTC-USD", "ETH-USD")
BASE = "https://api.exchange.coinbase.com/products/"
STOP = threading.Event()

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)

class Ledger:
    def __init__(self,path):
        self.db=sqlite3.connect(path,timeout=10,isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS evidence(seq INTEGER PRIMARY KEY,event_id TEXT UNIQUE,at REAL,kind TEXT,body TEXT,previous TEXT,digest TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS heartbeat(id INTEGER PRIMARY KEY CHECK(id=1),at REAL,status TEXT)")
    def append(self,kind,body):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row=self.db.execute("SELECT digest FROM evidence ORDER BY seq DESC LIMIT 1").fetchone()
            previous=row[0] if row else "0"*64
            event={"event_id":str(uuid.uuid4()),"at":time.time(),"kind":kind,"body":body,"previous":previous}
            digest=hashlib.sha256(canonical(event).encode()).hexdigest()
            self.db.execute("INSERT INTO evidence(event_id,at,kind,body,previous,digest) VALUES(?,?,?,?,?,?)",(event["event_id"],event["at"],kind,canonical(body),previous,digest))
            self.db.execute("INSERT INTO heartbeat VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET at=excluded.at,status=excluded.status",(event["at"],kind))
            self.db.execute("COMMIT")
            return digest
        except Exception:
            self.db.execute("ROLLBACK")
            raise
    def verify(self):
        previous="0"*64
        for event_id,at,kind,body,parent,digest in self.db.execute("SELECT event_id,at,kind,body,previous,digest FROM evidence ORDER BY seq"):
            event={"event_id":event_id,"at":at,"kind":kind,"body":json.loads(body),"previous":parent}
            if parent!=previous or hashlib.sha256(canonical(event).encode()).hexdigest()!=digest:
                return False
            previous=digest
        return True
    def close(self):
        self.db.close()

def assess(data,now=None):
    now=time.time() if now is None else now
    markets=[]
    for product in PRODUCTS:
        book=data[product]
        if book.get("auction_mode",False): raise ValueError("auction_mode")
        stamp=datetime.fromisoformat(book["time"].replace("Z","+00:00"))
        if stamp.tzinfo is None: raise ValueError("missing_timezone")
        age=now-stamp.timestamp()
        if age < -5 or age > 30: raise ValueError("stale_or_future_book")
        bid,bs=(Decimal(str(x)) for x in book["bids"][0][:2])
        ask,az=(Decimal(str(x)) for x in book["asks"][0][:2])
        if not all(x.is_finite() and x>0 for x in (bid,bs,ask,az)) or bid>ask:
            raise ValueError("invalid_book")
        markets.append({"product":product,"source":BASE+product+"/book?level=1","exchange_time":book["time"],"sequence":book["sequence"],"bid":str(bid),"bid_size":str(bs),"ask":str(ask),"ask_size":str(az),"spread":str(ask-bid),"executable":False})
    return {"venue":"Coinbase Exchange public market data","markets":markets,"status":"market_access_observed_not_account_or_execution_verified","revenue_verified":False}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): raise ValueError("redirect_rejected")

def fetch():
    result={}
    opener=urllib.request.build_opener(NoRedirect())
    for product in PRODUCTS:
        req=urllib.request.Request(BASE+product+"/book?level=1",headers={"User-Agent":"VennattaResearch/0.4","Accept":"application/json"})
        with opener.open(req,timeout=10) as response:
            if response.status!=200: raise ValueError("unexpected_http_status")
            raw=response.read(262145)
        if len(raw)>262144: raise ValueError("response_too_large")
        result[product]=json.loads(raw)
    return result

def cycle(ledger,fetcher=fetch):
    started=time.monotonic()
    try:
        report=assess(fetcher())
        if time.monotonic()-started>15: raise ValueError("slow_observation")
        kind="OBSERVATION"
    except Exception as exc:
        kind,report="ERROR",{"reason_type":type(exc).__name__,"reason":str(exc) if isinstance(exc,ValueError) and str(exc) in {"auction_mode","missing_timezone","stale_or_future_book","invalid_book","redirect_rejected","unexpected_http_status","response_too_large","slow_observation"} else "market_read_failed","revenue_verified":False}
    digest=ledger.append(kind,report)
    print(canonical({"event":kind,"digest":digest,"report":report}),flush=True)
    return kind=="OBSERVATION"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--state",default="state")
    p.add_argument("--once",action="store_true")
    args=p.parse_args()
    os.umask(0o077)
    state=Path(args.state);state.mkdir(parents=True,exist_ok=True)
    lock=(state/"node.lock").open("a")
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    ledger=Ledger(state/"evidence.sqlite3")
    if not ledger.verify():
        ledger.close();raise RuntimeError("Evidence verification failed")
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *_:STOP.set())
    failures=0
    try:
        while not STOP.is_set():
            if (state/"STOP").exists():
                ledger.append("STOPPED",{"reason":"persistent_kill_switch"});break
            okay=cycle(ledger)
            failures=0 if okay else min(failures+1,6)
            if args.once:return 0 if okay else 1
            STOP.wait(min(3600,60*2**failures))
    finally:
        ledger.close();lock.close()
    return 0

if __name__=="__main__":raise SystemExit(main())
