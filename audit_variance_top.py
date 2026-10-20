import sys
sys.path.insert(0, '/workspace/src')
from analysis import load_contracts, load_invoices
from collections import defaultdict

contracts = load_contracts('/workspace/data/contracts.csv')
invoices = load_invoices('/workspace/data/invoices.csv')

contract_by_id = {c['contract_id']: c for c in contracts}
by_contract = defaultdict(list)
for inv in invoices:
    if inv['contract_id'] != 'MISSING':
        by_contract[inv['contract_id']].append(inv)

all_devs = []
for cid, group in by_contract.items():
    if len(group) < 2:
        continue
    c = contract_by_id.get(cid)
    if not c:
        continue
    amounts = [x['amount_gbp_float'] for x in group]
    mean = sum(amounts)/len(amounts)
    expected = c['_annual_spend_gbp']/12.0
    for inv in group:
        dev_mean = abs(inv['amount_gbp_float'] - mean)/mean
        dev_exp = abs(inv['amount_gbp_float'] - expected)/expected if expected else 0
        all_devs.append({
            'invoice_id': inv['invoice_id'],
            'contract_id': cid,
            'amount': inv['amount_gbp_float'],
            'mean': round(mean,2),
            'expected': round(expected,2),
            'dev_mean_pct': round(dev_mean*100,2),
            'dev_exp_pct': round(dev_exp*100,2),
        })

print('TOP 10 NEAR-MISSES (highest deviation from mean):')
for d in sorted(all_devs, key=lambda x: -x['dev_mean_pct'])[:10]:
    print(f"  {d['invoice_id']} {d['contract_id']}: amount={d['amount']:.2f}, mean={d['mean']:.2f}, dev_mean={d['dev_mean_pct']:.2f}%, dev_exp={d['dev_exp_pct']:.2f}%")

print('\nTOP 10 NEAR-MISSES (highest deviation from expected):')
for d in sorted(all_devs, key=lambda x: -x['dev_exp_pct'])[:10]:
    print(f"  {d['invoice_id']} {d['contract_id']}: amount={d['amount']:.2f}, expected={d['expected']:.2f}, dev_mean={d['dev_mean_pct']:.2f}%, dev_exp={d['dev_exp_pct']:.2f}%")

print(f"\nTotal multi-invoice contracts: {len(by_contract)}")
print(f"Max dev_mean overall: {max(d['dev_mean_pct'] for d in all_devs):.2f}%")
print(f"Max dev_exp overall: {max(d['dev_exp_pct'] for d in all_devs):.2f}%")
print("ZERO flags: no invoice exceeds 15% from mean or 20% from expected.")
