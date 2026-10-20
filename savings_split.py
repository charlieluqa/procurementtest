import sys
sys.path.insert(0, '/workspace/src')
from analysis import load_contracts, _price_outlier_analysis
contracts = load_contracts('/workspace/data/contracts.csv')
all_out = _price_outlier_analysis(contracts, dedupe=False)
annual = [o for o in all_out if o['benchmark']=='annual_spend_median']
unit   = [o for o in all_out if o['benchmark']=='unit_price_median']
a_ids = {o['contract_id'] for o in annual}
u_ids = {o['contract_id'] for o in unit}
vol_only = a_ids - u_ids
price_only = u_ids - a_ids
both = a_ids & u_ids
print('ANNUAL ALL (12):', len(annual), 'total', sum(o['potential_saving_to_median_gbp'] for o in annual))
print('UNIT ALL (13):', len(unit), 'total', sum(o['potential_saving_to_median_gbp'] for o in unit))
print('VOLUME-ONLY (7):', len(vol_only), 'total', sum(o['potential_saving_to_median_gbp'] for o in annual if o['contract_id'] in vol_only))
print('PRICE-ONLY (8):', len(price_only), 'total', sum(o['potential_saving_to_median_gbp'] for o in unit if o['contract_id'] in price_only))
print('BOTH (5):')
for cid in sorted(both):
    a = next(o for o in annual if o['contract_id']==cid)
    u = next(o for o in unit if o['contract_id']==cid)
    print(f"  {cid}: annual_saving={a['potential_saving_to_median_gbp']:.2f}, unit_saving={u['potential_saving_to_median_gbp']:.2f}")
print('BOTH annual total:', sum(o['potential_saving_to_median_gbp'] for o in annual if o['contract_id'] in both))
print('BOTH unit total:', sum(o['potential_saving_to_median_gbp'] for o in unit if o['contract_id'] in both))
