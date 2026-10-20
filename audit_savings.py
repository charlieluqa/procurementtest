import sys
sys.path.insert(0, '/workspace/src')
from analysis import load_contracts
from collections import defaultdict

contracts = load_contracts('/workspace/data/contracts.csv')
by_service = defaultdict(list)
for c in contracts:
    by_service[c['service_code']].append(c)

results = []
for svc, group in by_service.items():
    if len(group) < 2:
        continue
    # Compute annual-spend median (current dashboard formula)
    annual_spends = sorted([x['_annual_spend_gbp'] for x in group])
    median_spend = annual_spends[len(annual_spends)//2]
    # Compute unit-price median
    unit_prices = sorted([float(x['price_per_unit_gbp']) for x in group])
    median_unit_price = unit_prices[len(unit_prices)//2]
    min_unit_price = min(unit_prices)
    max_unit_price = max(unit_prices)
    if max_unit_price == min_unit_price:
        continue
    for c in group:
        spend = c['_annual_spend_gbp']
        up = float(c['price_per_unit_gbp'])
        units = int(c['annual_units'])
        if up == max_unit_price:
            saving_spend_median = spend - median_spend
            # Unit-price benchmark: what would annual spend be at median unit price?
            hypothetical_median_spend = units * median_unit_price
            saving_unit_median = spend - hypothetical_median_spend
            hypothetical_min_spend = units * min_unit_price
            saving_unit_min = spend - hypothetical_min_spend
            results.append({
                'contract_id': c['contract_id'],
                'service_code': svc,
                'trust': c['trust'],
                'supplier': c['_canonical_supplier'],
                'annual_spend': round(spend, 2),
                'unit_price': up,
                'units': units,
                'median_spend': round(median_spend, 2),
                'saving_spend_median': round(saving_spend_median, 2),
                'median_unit_price': median_unit_price,
                'hypothetical_median_spend': round(hypothetical_median_spend, 2),
                'saving_unit_median': round(saving_unit_median, 2),
                'min_unit_price': min_unit_price,
                'hypothetical_min_spend': round(hypothetical_min_spend, 2),
                'saving_unit_min': round(saving_unit_min, 2),
            })

results.sort(key=lambda x: x['saving_spend_median'], reverse=True)
print('CONSOLIDATION SAVINGS (12 contracts flagged):')
for r in results:
    print(f"  {r['contract_id']} {r['service_code']}: annual={r['annual_spend']:.2f}, median_spend={r['median_spend']:.2f}, saving_spend_median={r['saving_spend_median']:.2f}")
    print(f"    unit_price={r['unit_price']:.4f}, median_unit_price={r['median_unit_price']:.4f}, hypothetical_median={r['hypothetical_median_spend']:.2f}, saving_unit_median={r['saving_unit_median']:.2f}")

print(f"\nTOTAL saving_spend_median: {sum(r['saving_spend_median'] for r in results):.2f}")
print(f"TOTAL saving_unit_median:  {sum(r['saving_unit_median'] for r in results):.2f}")
print(f"TOTAL saving_unit_min:     {sum(r['saving_unit_min'] for r in results):.2f}")
