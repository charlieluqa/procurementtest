import json, sys
sys.path.insert(0, '/workspace/src')
from analysis import (
    load_contracts, load_invoices,
    compute_executive_summary,
    all_findings,
    find_duplicate_invoice_ids,
    find_price_outliers,
    find_renewal_risks,
    find_unmapped_invoices,
    find_resubmitted_invoices,
    find_invoice_variance_vs_contract,
)

contracts = load_contracts('/workspace/data/contracts.csv')
invoices = load_invoices('/workspace/data/invoices.csv')

summary = compute_executive_summary(contracts, invoices)
findings = all_findings(contracts, invoices)

compact_contracts = [
    {
        "id": c["contract_id"],
        "trust": c["trust"],
        "category": c["category"],
        "service_code": c["service_code"],
        "supplier": c["_canonical_supplier"],
        "annual_spend": round(c["_annual_spend_gbp"], 2),
        "start": str(c["start_date_dt"]),
        "end": str(c["end_date_dt"]),
        "notice_days": c["notice_days_int"],
        "auto_renew": c["auto_renew"],
        "evidence": c["evidence_file"],
        "units": int(c["annual_units"]),
        "unit_price": float(c["price_per_unit_gbp"]),
        "unit_type": c["unit_type"],
    }
    for c in contracts
]

compact_invoices = [
    {
        "id": inv["invoice_id"],
        "contract_id": inv["contract_id"],
        "supplier": inv["_canonical_supplier"],
        "date": str(inv["invoice_date_dt"]),
        "amount": inv["amount_gbp_float"],
        "desc": inv["line_description"],
        "source": inv["source_file"],
        "resubmitted": inv["_is_resubmitted"],
    }
    for inv in invoices
]

payload = {
    "summary": summary,
    "findings": findings,
    "contracts": compact_contracts,
    "invoices": compact_invoices,
}

with open('/workspace/dashboard_payload.json', 'w') as f:
    json.dump(payload, f)

print('Saved dashboard_payload.json')
