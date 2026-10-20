"""Acceptance tests for a Cosine-built NHS procurement analysis prototype."""
import unittest
from pathlib import Path
from datetime import date
from src.analysis import load_contracts, load_invoices, find_duplicate_invoice_ids, find_price_outliers, find_renewal_risks
ROOT = Path(__file__).resolve().parents[1]

class ProcurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts=load_contracts(ROOT/'data/contracts.csv')
        cls.invoices=load_invoices(ROOT/'data/invoices.csv')

    def test_contract_count(self):
        self.assertEqual(len(self.contracts),49)

    def test_duplicate_candidates_exist(self):
        results=find_duplicate_invoice_ids(self.invoices)
        self.assertGreaterEqual(len(results),6)

    def test_price_variance_has_contract_evidence(self):
        results=find_price_outliers(self.contracts)
        self.assertTrue(results)
        self.assertTrue(all('contract' in str(x).lower() or 'source' in str(x).lower() for x in results))

    def test_renewal_risks_flagged(self):
        results=find_renewal_risks(self.contracts,date(2026,10,20))
        self.assertTrue(results)

if __name__=='__main__':unittest.main()
