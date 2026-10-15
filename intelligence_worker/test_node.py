import importlib.util,pathlib,tempfile,time,unittest
from datetime import datetime,timezone
spec=importlib.util.spec_from_file_location("node",pathlib.Path(__file__).with_name("node.py"))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
class Tests(unittest.TestCase):
    def fixture(self,offset=0):
        stamp=datetime.fromtimestamp(time.time()+offset,timezone.utc).isoformat()
        return {p:{"time":stamp,"sequence":1,"bids":[["100","2",1]],"asks":[["101","3",1]],"auction_mode":False} for p in n.PRODUCTS}
    def test_market_books(self):
        r=n.assess(self.fixture());self.assertEqual(len(r["markets"]),2)
        self.assertFalse(r["revenue_verified"]);self.assertTrue(all(not m["executable"] for m in r["markets"]))
    def test_stale_rejected(self):
        with self.assertRaises(ValueError):n.assess(self.fixture(-60))
    def test_future_rejected(self):
        with self.assertRaises(ValueError):n.assess(self.fixture(60))
    def test_zero_size_rejected(self):
        d=self.fixture();d["BTC-USD"]["bids"][0][1]="0"
        with self.assertRaises(ValueError):n.assess(d)
    def test_auction_rejected(self):
        d=self.fixture();d["BTC-USD"]["auction_mode"]=True
        with self.assertRaises(ValueError):n.assess(d)
    def test_persistence_and_edit(self):
        with tempfile.TemporaryDirectory() as d:
            path=pathlib.Path(d)/"db";l=n.Ledger(path);l.append("OBSERVATION",{"x":1});l.close()
            l=n.Ledger(path);self.assertTrue(l.verify());l.append("ERROR",{});self.assertTrue(l.verify())
            l.db.execute("UPDATE evidence SET body='{}' WHERE seq=1");self.assertFalse(l.verify());l.close()
    def test_online_cycle_failure_not_success(self):
        with tempfile.TemporaryDirectory() as d:
            l=n.Ledger(pathlib.Path(d)/"db");self.assertTrue(n.cycle(l,self.fixture))
            self.assertFalse(n.cycle(l,lambda:{}));self.assertEqual(l.db.execute("SELECT status FROM heartbeat").fetchone()[0],"ERROR");l.close()
if __name__=="__main__":unittest.main()
