"""NHS-style procurement intelligence analysis — deterministic, provenance-aware.

All data synthetic.  Calculations are exact from CSV values.
"""
from __future__ import annotations
import csv
from pathlib import Path
from datetime import date, datetime, timedelta
from collections import defaultdict


AS_OF = date(2026, 10, 20)

SUPPLIER_ALIASES = {
    "medi flow ltd": "MediFlow",
    "mediflow solutions": "MediFlow",
    "mediflow solutions uk": "MediFlow",
    "wardlink technologies": "WardLink",
    "ward link tech": "WardLink",
    "nimble cloud uk": "NimbleCloud",
    "nimblecloud uk": "NimbleCloud",
    "staff orbit limited": "StaffOrbit",
    "stafforbit ltd": "StaffOrbit",
    "interop works": "InteropWorks",
    "interopworks plc": "InteropWorks",
    "clinicconnect ltd": "ClinicConnect",
    "clinic connect uk ltd": "ClinicConnect",
    "voxica systems": "Voxica Systems",
    "pulsebridge health": "PulseBridge Health",
    "carelingo uk": "CareLingo UK",
    "sentinelpoint consulting": "SentinelPoint Consulting",
    "nhs analytics lab": "NHS Analytics Lab",
    "unmapped vendor": "Unmapped Vendor",
}


def _norm_supplier(name: str) -> str:
    key = name.strip().lower()
    return SUPPLIER_ALIASES.get(key, name.strip())


def load_contracts(path: str | Path) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["_annual_spend_gbp"] = float(r["annual_units"]) * float(r["price_per_unit_gbp"])
            r["_canonical_supplier"] = _norm_supplier(r["supplier_name"])
            r["start_date_dt"] = datetime.strptime(r["start_date"], "%Y-%m-%d").date()
            r["end_date_dt"] = datetime.strptime(r["end_date"], "%Y-%m-%d").date()
            r["notice_days_int"] = int(r["notice_days"])
            rows.append(r)
    return rows


def load_invoices(path: str | Path) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["amount_gbp_float"] = float(r["amount_gbp"])
            r["invoice_date_dt"] = datetime.strptime(r["invoice_date"], "%Y-%m-%d").date()
            r["_canonical_supplier"] = _norm_supplier(r["supplier_name"])
            r["_is_resubmitted"] = "resubmitted" in r.get("source_file", "").lower()
            rows.append(r)
    return rows


def find_duplicate_invoice_ids(invoices: list[dict]) -> list[dict]:
    """Return exact-duplicate or resubmitted invoice_id collisions with evidence."""
    by_id: dict[str, list[dict]] = defaultdict(list)
    for inv in invoices:
        by_id[inv["invoice_id"]].append(inv)

    results = []
    for inv_id, group in by_id.items():
        if len(group) > 1:
            total_amount = sum(x["amount_gbp_float"] for x in group)
            resub_count = sum(1 for x in group if x["_is_resubmitted"])
            normal_count = len(group) - resub_count
            results.append({
                "invoice_id": inv_id,
                "occurrences": len(group),
                "total_amount_gbp": round(total_amount, 2),
                "resubmitted_count": resub_count,
                "normal_count": normal_count,
                "contract_ids": sorted({x["contract_id"] for x in group}),
                "invoice_dates": sorted({str(x["invoice_date_dt"]) for x in group}),
                "source_files": [x["source_file"] for x in group],
                "finding_type": "duplicate_invoice_id",
            })
    return results


def find_price_outliers(contracts: list[dict]) -> list[dict]:
    """Compare unit rates for identical service_codes across trusts.
    Flag highest-price contracts with potential savings if aligned to median/lowest."""
    by_service: dict[str, list[dict]] = defaultdict(list)
    for c in contracts:
        by_service[c["service_code"]].append(c)

    results = []
    for svc, group in by_service.items():
        if len(group) < 2:
            continue
        rates = [x["_annual_spend_gbp"] for x in group]
        min_rate = min(rates)
        max_rate = max(rates)
        median_rate = sorted(rates)[len(rates) // 2]
        if max_rate == min_rate:
            continue
        for c in group:
            spend = c["_annual_spend_gbp"]
            if spend == max_rate:
                saving_to_median = spend - median_rate
                saving_to_min = spend - min_rate
                results.append({
                    "finding_type": "price_variance_high",
                    "service_code": svc,
                    "category": c["category"],
                    "contract_id": c["contract_id"],
                    "trust": c["trust"],
                    "supplier_canonical": c["_canonical_supplier"],
                    "annual_spend_gbp": round(spend, 2),
                    "median_spend_gbp": round(median_rate, 2),
                    "lowest_spend_gbp": round(min_rate, 2),
                    "potential_saving_to_median_gbp": round(saving_to_median, 2),
                    "potential_saving_to_lowest_gbp": round(saving_to_min, 2),
                    "price_per_unit_gbp": float(c["price_per_unit_gbp"]),
                    "annual_units": int(c["annual_units"]),
                    "source": f"contract {c['contract_id']} ({c['evidence_file']})",
                })
    # Sort by potential saving desc
    results.sort(key=lambda x: x["potential_saving_to_median_gbp"], reverse=True)
    return results


def find_renewal_risks(contracts: list[dict], as_of: date = AS_OF) -> list[dict]:
    """Flag contracts where notice deadline has passed or end date is within 90 days."""
    results = []
    for c in contracts:
        end = c["end_date_dt"]
        notice = c["notice_days_int"]
        deadline = end - timedelta(days=notice)  # latest day notice can be given
        days_to_end = (end - as_of).days
        days_past_deadline = (as_of - deadline).days

        status = "ok"
        if days_to_end < 0:
            status = "expired"
        elif days_past_deadline > 0:
            status = "notice_missed" if c["auto_renew"] == "No" else "auto_renew_imminent"
        elif days_to_end <= 90:
            status = "renewal_soon"

        if status != "ok":
            results.append({
                "finding_type": "renewal_risk",
                "contract_id": c["contract_id"],
                "trust": c["trust"],
                "supplier_canonical": c["_canonical_supplier"],
                "category": c["category"],
                "end_date": str(end),
                "notice_days": notice,
                "notice_deadline": str(deadline),
                "auto_renew": c["auto_renew"],
                "days_to_end": days_to_end,
                "days_past_deadline": days_past_deadline,
                "status": status,
                "annual_spend_gbp": round(c["_annual_spend_gbp"], 2),
                "source": f"contract {c['contract_id']} ({c['evidence_file']})",
            })
    # Sort severity: expired > notice_missed > auto_renew_imminent > renewal_soon
    severity_order = {"expired": 0, "notice_missed": 1, "auto_renew_imminent": 2, "renewal_soon": 3}
    results.sort(key=lambda x: (severity_order[x["status"]], -x["days_to_end"]))
    return results


def find_unmapped_invoices(invoices: list[dict]) -> list[dict]:
    return [
        {
            "finding_type": "unmapped_invoice",
            "invoice_id": inv["invoice_id"],
            "invoice_date": str(inv["invoice_date_dt"]),
            "amount_gbp": inv["amount_gbp_float"],
            "supplier_canonical": inv["_canonical_supplier"],
            "source_file": inv["source_file"],
        }
        for inv in invoices
        if inv["contract_id"] == "MISSING"
    ]


def find_invoice_variance_vs_contract(invoices: list[dict], contracts: list[dict]) -> list[dict]:
    """For contracts with >1 invoice, flag months where amount deviates >15% from mean."""
    contract_by_id = {c["contract_id"]: c for c in contracts}
    by_contract: dict[str, list[dict]] = defaultdict(list)
    for inv in invoices:
        if inv["contract_id"] != "MISSING":
            by_contract[inv["contract_id"]].append(inv)

    results = []
    for cid, group in by_contract.items():
        if len(group) < 2:
            continue
        c = contract_by_id.get(cid)
        if not c:
            continue
        amounts = [x["amount_gbp_float"] for x in group]
        mean_amt = sum(amounts) / len(amounts)
        if mean_amt == 0:
            continue
        expected_monthly = c["_annual_spend_gbp"] / 12.0
        for inv in group:
            dev = abs(inv["amount_gbp_float"] - mean_amt) / mean_amt
            dev_expected = abs(inv["amount_gbp_float"] - expected_monthly) / expected_monthly if expected_monthly else 0
            if dev > 0.15 or dev_expected > 0.20:
                results.append({
                    "finding_type": "invoice_variance",
                    "contract_id": cid,
                    "trust": c["trust"],
                    "supplier_canonical": inv["_canonical_supplier"],
                    "invoice_id": inv["invoice_id"],
                    "invoice_date": str(inv["invoice_date_dt"]),
                    "amount_gbp": inv["amount_gbp_float"],
                    "mean_amount_gbp": round(mean_amt, 2),
                    "expected_monthly_gbp": round(expected_monthly, 2),
                    "deviation_from_mean_pct": round(dev * 100, 1),
                    "deviation_from_expected_pct": round(dev_expected * 100, 1),
                    "source": f"invoice {inv['invoice_id']} ({inv['source_file']})",
                })
    return results


def find_resubmitted_invoices(invoices: list[dict]) -> list[dict]:
    return [
        {
            "finding_type": "resubmitted_invoice",
            "invoice_id": inv["invoice_id"],
            "contract_id": inv["contract_id"],
            "invoice_date": str(inv["invoice_date_dt"]),
            "amount_gbp": inv["amount_gbp_float"],
            "supplier_canonical": inv["_canonical_supplier"],
            "source_file": inv["source_file"],
        }
        for inv in invoices
        if inv["_is_resubmitted"]
    ]


def compute_executive_summary(contracts: list[dict], invoices: list[dict]) -> dict:
    total_annual_spend = sum(c["_annual_spend_gbp"] for c in contracts)
    total_invoiced = sum(inv["amount_gbp_float"] for inv in invoices)
    dupes = find_duplicate_invoice_ids(invoices)
    unmapped = find_unmapped_invoices(invoices)
    resubmitted = find_resubmitted_invoices(invoices)
    renewals = find_renewal_risks(contracts)
    price_outliers = find_price_outliers(contracts)
    variance = find_invoice_variance_vs_contract(invoices, contracts)

    duplicate_recovery = sum(d["total_amount_gbp"] for d in dupes)
    unmapped_exposure = sum(u["amount_gbp"] for u in unmapped)
    resubmitted_exposure = sum(r["amount_gbp"] for r in resubmitted)

    # Savings: only count median-based savings for unique contracts flagged as high-price
    savings_contracts = {p["contract_id"] for p in price_outliers}
    potential_consolidation = sum(
        p["potential_saving_to_median_gbp"] for p in price_outliers
    )

    return {
        "as_of": str(AS_OF),
        "contract_count": len(contracts),
        "invoice_count": len(invoices),
        "total_annual_contract_spend_gbp": round(total_annual_spend, 2),
        "total_invoiced_jan_jun_gbp": round(total_invoiced, 2),
        "upcoming_renewal_count": len(renewals),
        "duplicate_invoice_recovery_gbp": round(duplicate_recovery, 2),
        "unmapped_invoice_exposure_gbp": round(unmapped_exposure, 2),
        "resubmitted_invoice_exposure_gbp": round(resubmitted_exposure, 2),
        "invoice_variance_flags": len(variance),
        "potential_consolidation_savings_gbp": round(potential_consolidation, 2),
        "savings_at_risk_contracts": len(savings_contracts),
        "confirmed_discrepancies": len(dupes) + len(unmapped) + len(resubmitted),
        "potential_recoveries": len(dupes),
        "unvalidated_savings_opportunities": len(price_outliers),
    }


def all_findings(contracts: list[dict], invoices: list[dict]) -> list[dict]:
    """Ranked union of every finding for dashboard consumption."""
    out = []
    for f in find_duplicate_invoice_ids(invoices):
        f["severity"] = "confirmed"
        f["financial_value_gbp"] = f["total_amount_gbp"]
        f["title"] = f"Duplicate invoice ID {f['invoice_id']} ({f['occurrences']} occurrences)"
        out.append(f)
    for f in find_unmapped_invoices(invoices):
        f["severity"] = "confirmed"
        f["financial_value_gbp"] = f["amount_gbp"]
        f["title"] = f"Unmapped invoice {f['invoice_id']} — {f['supplier_canonical']}"
        out.append(f)
    for f in find_resubmitted_invoices(invoices):
        f["severity"] = "potential"
        f["financial_value_gbp"] = f["amount_gbp"]
        f["title"] = f"Resubmitted invoice {f['invoice_id']} — review for duplicate payment"
        out.append(f)
    for f in find_invoice_variance_vs_contract(invoices, contracts):
        f["severity"] = "potential"
        f["financial_value_gbp"] = f["amount_gbp"]
        f["title"] = f"Invoice variance {f['invoice_id']} (dev {f['deviation_from_mean_pct']}%)"
        out.append(f)
    for f in find_renewal_risks(contracts):
        f["severity"] = "risk"
        f["financial_value_gbp"] = f["annual_spend_gbp"]
        f["title"] = f"Renewal risk {f['contract_id']} — {f['status'].replace('_', ' ')}"
        out.append(f)
    for f in find_price_outliers(contracts):
        f["severity"] = "opportunity"
        f["financial_value_gbp"] = f["potential_saving_to_median_gbp"]
        f["title"] = f"Savings opportunity {f['contract_id']} ({f['service_code']}) over median by GBP {f['potential_saving_to_median_gbp']:,.2f}"
        out.append(f)
    out.sort(key=lambda x: (-{"confirmed": 3, "potential": 2, "risk": 1, "opportunity": 0}[x["severity"]], x["financial_value_gbp"]), reverse=True)
    return out
