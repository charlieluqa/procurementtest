import sys, json
sys.path.insert(0, '/workspace/src')
from analysis import load_contracts, load_invoices, compute_executive_summary

contracts = load_contracts('/workspace/data/contracts.csv')
invoices = load_invoices('/workspace/data/invoices.csv')

s = compute_executive_summary(contracts, invoices)
print(json.dumps(s, indent=2))
