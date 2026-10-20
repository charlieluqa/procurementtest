"""Replace this stub with tested, provenance-aware procurement analysis.

Do not hardcode synthetic anomaly identifiers. Document assumptions and
return explainable results with contract/invoice references.
"""

from pathlib import Path

def load_contracts(path: str | Path):
    raise NotImplementedError("Implement CSV reading and validation")

def load_invoices(path: str | Path):
    raise NotImplementedError("Implement CSV reading and validation")

def find_duplicate_invoice_ids(invoices):
    raise NotImplementedError("Implement evidence-based suspected duplicates")

def find_price_outliers(contracts):
    raise NotImplementedError("Compare unit rates only for identical service codes")

def find_renewal_risks(contracts, as_of):
    raise NotImplementedError("Respect end date and notice periods")
