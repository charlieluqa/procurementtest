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

THRESHOLD_MEAN = 0.15
THRESHOLD_EXPECTED = 0.20

print(f'THRESHOLDS: dev_from_mean > {THRESHOLD_MEAN*100:.0f}% OR dev_from_expected > {THRESHOLD_EXPECTED*100:.0f}%')
print()

flags = []
close = []
for cid, group in by_contract.items():
    if len(group) < 2:
        continue
    c = contract_by_id.get(cid)
    if not c:
        continue
    amounts = [x['amount_gbp_float'] for x in group]
    mean = sum(amounts)/len(amounts)
    expected = c['_annual_spend_gbp']/12.0
    if mean == 0:
        continue
    for inv in group:
        dev_mean = abs(inv['amount_gbp_float'] - mean)/mean
        dev_exp = abs(inv['amount_gbp_float'] - expected)/expected if expected else 0
        if dev_mean > THRESHOLD_MEAN or dev_exp > THRESHOLD_EXPECTED:
            flags.append({
                'invoice_id': inv['invoice_id'],
                'contract_id': cid,
                'amount': inv['amount_gbp_float'],
                'mean': round(mean,2),
                'expected': round(expected,2),
                'dev_mean_pct': round(dev_mean*100,2),
                'dev_exp_pct': round(dev_exp*100,2),
            })
        elif max(dev_mean, dev_exp) > 0.10:
            close.append({
                'invoice_id': inv['invoice_id'],
                'contract_id': cid,
                'amount': inv['amount_gbp_float'],
                'mean': round(mean,2),
                'expected': round(expected,2),
                'dev_mean_pct': round(dev_mean*100,2),
                'dev_exp_pct': round(dev_exp*100,2),
            })

print(f'VARIANCE FLAGS: {len(flags)}')
for f in flags:
    print(f"  {f['invoice_id']} {f['contract_id']}: amount={f['amount']:.2f}, mean={f['mean']:.2f}, expected={f['expected']:.2f}, dev_mean={f['dev_mean_pct']:.1f}%, dev_exp={f['dev_exp_pct']:.1f}%")

print(f'\nNEAR-MISSES (>10% but <= thresholds): {len(close)}')
for f in sorted(close, key=lambda x: -max(x['dev_mean_pct'], x['dev_exp_pct']))[:15]:
    print(f"  {f['invoice_id']} {f['contract_id']}: amount={f['amount']:.2f}, mean={f['mean']:.2f}, expected={f['expected']:.2f}, dev_mean={f['dev_mean_pct']:.2f}%, dev_exp={f['dev_exp_pct']:.2f}%")

# Summary of max deviations per contract
print('\nMAX DEVIATION PER MULTI-INVOICE CONTRACT:')
for cid in sorted(by_contract.keys()):
    group = by_contract[cid]
    if len(group) < 2:
        continue
    c = contract_by_id.get(cid)
    amounts = [x['amount_gbp_float'] for x in group]
    mean = sum(amounts)/len(amounts)
    expected = c['_annual_spend_gbp']/12.0 if c else 0
    max_dev_mean = max(abs(x-mean)/mean for x in amounts)
    max_dev_exp = max(abs(x-expected)/expected for x in amounts) if expected else 0
    print(f"  {cid}: max_dev_mean={max_dev_mean*100:.2f}%, max_dev_exp={max_dev_exp*100:.2f}%")
