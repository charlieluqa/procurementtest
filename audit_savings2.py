import sys
sys.path.insert(0, '/workspace/src')
from analysis import load_contracts
from collections import defaultdict

contracts = load_contracts('/workspace/data/contracts.csv')
by_service = defaultdict(list)
for c in contracts:
    by_service[c['service_code']].append(c)

# Old formula: max_annual_spend - median_annual_spend per service
old_results = []
# New unit-price benchmark: for contracts with unit_price > median_unit_price,
# saving = actual_annual_spend - (units * median_unit_price)
unit_results = []

for svc, group in by_service.items():
    if len(group) < 2:
        continue
    annual_spends = sorted([x['_annual_spend_gbp'] for x in group])
    median_spend = annual_spends[len(annual_spends)//2]
    max_spend = max(annual_spends)

    unit_prices = sorted([float(x['price_per_unit_gbp']) for x in group])
    median_unit_price = unit_prices[len(unit_prices)//2]
    min_unit_price = min(unit_prices)

    for c in group:
        spend = c['_annual_spend_gbp']
        up = float(c['price_per_unit_gbp'])
        units = int(c['annual_units'])

        # OLD logic flags max annual spend only
        if spend == max_spend and max_spend != median_spend:
            old_results.append({
                'contract_id': c['contract_id'],
                'service_code': svc,
                'annual_spend': round(spend,2),
                'median_spend': round(median_spend,2),
                'saving': round(spend - median_spend,2),
                'unit_price': up,
                'median_unit_price': median_unit_price,
                'units': units,
                'volume_driven': up <= median_unit_price,  # if unit price not above median, flagged only due to volume
            })

        # UNIT-PRICE benchmark: flag if unit_price > median_unit_price
        if up > median_unit_price:
            hypothetical = units * median_unit_price
            saving = spend - hypothetical
            unit_results.append({
                'contract_id': c['contract_id'],
                'service_code': svc,
                'annual_spend': round(spend,2),
                'hypothetical_median': round(hypothetical,2),
                'saving': round(saving,2),
                'unit_price': up,
                'median_unit_price': median_unit_price,
                'units': units,
            })

print('=== OLD FORMULA (max annual spend - median annual spend) ===')
for r in sorted(old_results, key=lambda x: -x['saving']):
    print(f"  {r['contract_id']} {r['service_code']}: annual={r['annual_spend']:.2f}, median={r['median_spend']:.2f}, saving={r['saving']:.2f}, unit={r['unit_price']:.4f}, median_unit={r['median_unit_price']:.4f}, volume_driven={r['volume_driven']}")
print(f"  TOTAL old saving: {sum(r['saving'] for r in old_results):.2f}")
print(f"  Count: {len(old_results)}")

print('\n=== UNIT-PRICE BENCHMARK (unit_price > median_unit_price, saving = annual - units*median_unit) ===')
for r in sorted(unit_results, key=lambda x: -x['saving']):
    print(f"  {r['contract_id']} {r['service_code']}: annual={r['annual_spend']:.2f}, hypo={r['hypothetical_median']:.2f}, saving={r['saving']:.2f}, unit={r['unit_price']:.4f}, median_unit={r['median_unit_price']:.4f}")
print(f"  TOTAL unit-price saving: {sum(r['saving'] for r in unit_results):.2f}")
print(f"  Count: {len(unit_results)}")

print('\n=== CONTRACTS IN OLD BUT NOT IN UNIT-PRICE (pure volume-driven) ===')
old_ids = {r['contract_id'] for r in old_results}
unit_ids = {r['contract_id'] for r in unit_results}
for cid in sorted(old_ids - unit_ids):
    r = next(x for x in old_results if x['contract_id']==cid)
    print(f"  {cid} {r['service_code']}: saving={r['saving']:.2f}, unit_price={r['unit_price']:.4f} <= median_unit={r['median_unit_price']:.4f}")

print('\n=== CONTRACTS IN UNIT-PRICE BUT NOT IN OLD (hidden price outliers) ===')
for cid in sorted(unit_ids - old_ids):
    r = next(x for x in unit_results if x['contract_id']==cid)
    print(f"  {cid} {r['service_code']}: saving={r['saving']:.2f}, unit_price={r['unit_price']:.4f} > median_unit={r['median_unit_price']:.4f}")
