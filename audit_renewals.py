import sys
sys.path.insert(0, '/workspace/src')
from analysis import load_contracts
from datetime import date

contracts = load_contracts('/workspace/data/contracts.csv')
as_of = date(2026, 10, 20)
look_ahead = 90  # days

print(f'AS OF: {as_of}')
print(f'LOOK-AHEAD: {look_ahead} days (renewal_soon if <= 90 and not yet missed)')
print(f'NOTICE RULE: if today > deadline (end - notice_days), status = notice_missed (if auto_renew=No) or auto_renew_imminent (if auto_renew=Yes)')
print(f'             if today <= deadline and days_to_end <= 90, status = renewal_soon')
print(f'             if days_to_end < 0, status = expired')
print()

results = []
for c in contracts:
    end = c['end_date_dt']
    notice = c['notice_days_int']
    deadline = end - __import__('datetime').timedelta(days=notice)
    days_to_end = (end - as_of).days
    days_past_deadline = (as_of - deadline).days

    if days_to_end < 0:
        status = 'expired'
    elif days_past_deadline > 0:
        status = 'notice_missed' if c['auto_renew'] == 'No' else 'auto_renew_imminent'
    elif days_to_end <= look_ahead:
        status = 'renewal_soon'
    else:
        status = 'ok'

    if status != 'ok':
        results.append({
            'contract_id': c['contract_id'],
            'trust': c['trust'],
            'category': c['category'],
            'end': str(end),
            'notice': notice,
            'deadline': str(deadline),
            'auto_renew': c['auto_renew'],
            'days_to_end': days_to_end,
            'days_past_deadline': days_past_deadline,
            'status': status,
            'annual_spend': round(c['_annual_spend_gbp'], 2),
        })

# severity sort
order = {'expired':0, 'notice_missed':1, 'auto_renew_imminent':2, 'renewal_soon':3}
results.sort(key=lambda x: (order[x['status']], -x['days_to_end']))

for r in results:
    print(f"  {r['contract_id']:8s} | {r['status']:20s} | end={r['end']} | notice={r['notice']:3d}d | deadline={r['deadline']} | days_to_end={r['days_to_end']:4d} | days_past_deadline={r['days_past_deadline']:4d} | auto_renew={r['auto_renew']:3s} | spend=£{r['annual_spend']:,.2f}")

print(f"\nTOTAL flagged: {len(results)}")
print(f"  expired:            {sum(1 for x in results if x['status']=='expired')}")
print(f"  notice_missed:      {sum(1 for x in results if x['status']=='notice_missed')}")
print(f"  auto_renew_imminent:{sum(1 for x in results if x['status']=='auto_renew_imminent')}")
print(f"  renewal_soon:       {sum(1 for x in results if x['status']=='renewal_soon')}")
