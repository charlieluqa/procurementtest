import sys
sys.path.insert(0, '/workspace/src')
from analysis import load_invoices
from collections import defaultdict

invoices = load_invoices('/workspace/data/invoices.csv')
by_id = defaultdict(list)
for inv in invoices:
    by_id[inv['invoice_id']].append(inv)

dupes = [(k, v) for k, v in by_id.items() if len(v) > 1]
print('DUPLICATE INVOICE IDs:')
extra_total = 0.0
all_total = 0.0
for k, group in dupes:
    amounts = [x['amount_gbp_float'] for x in group]
    resub_flags = [x['_is_resubmitted'] for x in group]
    total = sum(amounts)
    all_total += total
    # The "additional duplicate record" value: if exactly one resubmitted among duplicates,
    # that resubmitted amount is the extra record. Otherwise, the amount beyond the first occurrence.
    resub_count = sum(resub_flags)
    normal_count = len(group) - resub_count
    if resub_count == 1 and normal_count >= 1:
        extra = amounts[resub_flags.index(True)]
    else:
        # general case: sum of all beyond the first original
        extra = total - amounts[0]
    extra_total += extra
    print(f"  {k}: occ={len(group)}, amounts={amounts}, resub={resub_flags}, total={total:.2f}, extra={extra:.2f}")

print(f'\nALL_TOTAL (combined record value): {all_total:.2f}')
print(f'EXTRA_TOTAL (additional duplicate records only): {extra_total:.2f}')
