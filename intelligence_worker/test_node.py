import importlib.util, pathlib, tempfile, unittest
spec=importlib.util.spec_from_file_location("node",pathlib.Path(__file__).with_name("node.py"))
n=importlib.util.module_from_spec(spec)
spec.loader.exec_module(n)

class NodeTests(unittest.TestCase):
    def fixture(self):
        return {"error":[],"result":{k:{"b":[b],"a":[a]} for k,b,a in [("XETHZUSD","1999","2000"),("XXBTZUSD","99900","100000"),("XETHXXBT",".0199",".0201")]}}

    def test_routes_not_trades(self):
        report=n.assess(self.fixture())
        self.assertEqual(len(report["gross_routes"]),2)
        self.assertFalse(report["revenue_verified"])
        self.assertTrue(all(not r["executable"] for r in report["gross_routes"]))

    def test_invalid_quote(self):
        data=self.fixture()
        data["result"]["XETHZUSD"]["b"]=["NaN"]
        with self.assertRaises(ValueError): n.assess(data)

    def test_provider_error(self):
        with self.assertRaises(ValueError): n.assess({"error":["failure"]})

    def test_reopen_and_chain(self):
        with tempfile.TemporaryDirectory() as d:
            path=pathlib.Path(d)/"db"
            ledger=n.Ledger(path)
            first=ledger.append("OBSERVATION",{"a":1})
            ledger.close()
            ledger=n.Ledger(path)
            second=ledger.append("OBSERVATION",{"a":2})
            self.assertNotEqual(first,second)
            self.assertTrue(ledger.verify())
            self.assertEqual(ledger.db.execute("SELECT previous FROM evidence WHERE seq=2").fetchone()[0],first)
            ledger.close()

    def test_detect_edit(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=n.Ledger(pathlib.Path(d)/"db")
            ledger.append("OBSERVATION",{"a":1})
            ledger.db.execute("UPDATE evidence SET body='{}' WHERE seq=1")
            self.assertFalse(ledger.verify())
            ledger.close()

    def test_success_then_error(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=n.Ledger(pathlib.Path(d)/"db")
            self.assertTrue(n.cycle(ledger,self.fixture))
            self.assertFalse(n.cycle(ledger,lambda:{"error":["failure"]}))
            self.assertEqual(ledger.db.execute("SELECT status FROM heartbeat").fetchone()[0],"ERROR")
            self.assertTrue(ledger.verify())
            ledger.close()

if __name__ == "__main__": unittest.main()
