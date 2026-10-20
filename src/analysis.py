"""NHS-style procurement intelligence analysis — deterministic, provenance-aware.

All data synthetic.  Calculations are exact from CSV values.
"""
from __future__ import annotations
import csv
from pathlib import Path
from datetime import date, datetime, timedelta
from collections import defaultdict


AS_OF = date(2026, 10, 20)
LOOK_AHEAD_DAYS = 90

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
    """Return exact-duplicate or resubmitted invoice_id collisions.

    total_amount_gbp = sum of all occurrences.
    additional_duplicate_value_gbp = value of the extra records only
    (if one resubmitted among duplicates, the resubmitted amount is the extra;
    otherwise sum beyond the first original).
    """
    by_id: dict[str, list[dict]] = defaultdict(list)
    for inv in invoices:
        by_id[inv["invoice_id"]].append(inv)

    results = []
    for inv_id, group in by_id.items():
        if len(group) <= 1:
            continue
        amounts = [x["amount_gbp_float"] for x in group]
        resub_flags = [x["_is_resubmitted"] for x in group]
        total = sum(amounts)
        resub_count = sum(resub_flags)
        normal_count = len(group) - resub_count

        if resub_count == 1 and normal_count >= 1:
            extra = amounts[resub_flags.index(True)]
        else:
            extra = total - amounts[0]

        results.append({
            "invoice_id": inv_id,
            "occurrences": len(group),
            "total_amount_gbp": round(total, 2),
            "additional_duplicate_value_gbp": round(extra, 2),
            "resubmitted_count": resub_count,
            "normal_count": normal_count,
            "contract_ids": sorted({x["contract_id"] for x in group}),
            "invoice_dates": sorted({str(x["invoice_date_dt"]) for x in group}),
            "source_files": [x["source_file"] for x in group],
            "finding_type": "duplicate_invoice_id",
        })
    return results


def _price_outlier_analysis(contracts: list[dict], dedupe: bool = False) -> list[dict]:
    """Core comparison: both annual-spend median and unit-price median.
    Flags two sets:
      - max_annual_spend contracts (old formula, can be volume-driven)
      - unit_price > median_unit_price contracts (true price outliers)
    If dedupe=True, only the preferred benchmark per contract is kept
    (unit-price wins when both exist).
    """
    by_service: dict[str, list[dict]] = defaultdict(list)
    for c in contracts:
        by_service[c["service_code"]].append(c)

    results = []
    for svc, group in by_service.items():
        if len(group) < 2:
            continue
        annual_spends = sorted([x["_annual_spend_gbp"] for x in group])
        unit_prices = sorted([float(x["price_per_unit_gbp"]) for x in group])
        min_annual = annual_spends[0]
        max_annual = annual_spends[-1]
        median_annual = annual_spends[len(annual_spends) // 2]
        min_unit = unit_prices[0]
        max_unit = unit_prices[-1]
        median_unit = unit_prices[len(unit_prices) // 2]

        if max_annual == min_annual and max_unit == min_unit:
            continue

        for c in group:
            spend = c["_annual_spend_gbp"]
            up = float(c["price_per_unit_gbp"])
            units = int(c["annual_units"])

            # annual-spend benchmark (can be volume-driven)
            if spend == max_annual and max_annual != median_annual:
                saving_spend_median = spend - median_annual
                saving_spend_min = spend - min_annual
                volume_driven = up <= median_unit
                results.append({
                    "benchmark": "annual_spend_median",
                    "finding_type": "price_variance_high",
                    "service_code": svc,
                    "category": c["category"],
                    "contract_id": c["contract_id"],
                    "trust": c["trust"],
                    "supplier_canonical": c["_canonical_supplier"],
                    "annual_spend_gbp": round(spend, 2),
                    "median_spend_gbp": round(median_annual, 2),
                    "lowest_spend_gbp": round(min_annual, 2),
                    "potential_saving_to_median_gbp": round(saving_spend_median, 2),
                    "potential_saving_to_lowest_gbp": round(saving_spend_min, 2),
                    "price_per_unit_gbp": up,
                    "median_unit_price_gbp": median_unit,
                    "lowest_unit_price_gbp": min_unit,
                    "annual_units": units,
                    "volume_driven": volume_driven,
                    "source": f"contract {c['contract_id']} ({c['evidence_file']})",
                })

            # unit-price benchmark (true rate outlier)
            if up > median_unit:
                hypothetical_median = units * median_unit
                saving_unit_median = spend - hypothetical_median
                hypothetical_min = units * min_unit
                saving_unit_min = spend - hypothetical_min
                results.append({
                    "benchmark": "unit_price_median",
                    "finding_type": "price_variance_high",
                    "service_code": svc,
                    "category": c["category"],
                    "contract_id": c["contract_id"],
                    "trust": c["trust"],
                    "supplier_canonical": c["_canonical_supplier"],
                    "annual_spend_gbp": round(spend, 2),
                    "median_spend_gbp": round(hypothetical_median, 2),
                    "lowest_spend_gbp": round(hypothetical_min, 2),
                    "potential_saving_to_median_gbp": round(saving_unit_median, 2),
                    "potential_saving_to_lowest_gbp": round(saving_unit_min, 2),
                    "price_per_unit_gbp": up,
                    "median_unit_price_gbp": median_unit,
                    "lowest_unit_price_gbp": min_unit,
                    "annual_units": units,
                    "volume_driven": False,
                    "source": f"contract {c['contract_id']} ({c['evidence_file']})",
                })

    if dedupe:
        seen = set()
        deduped = []
        for r in sorted(results, key=lambda x: (x["contract_id"], x["benchmark"] == "unit_price_median"), reverse=True):
            if r["contract_id"] not in seen:
                seen.add(r["contract_id"])
                deduped.append(r)
        deduped.sort(key=lambda x: (-(x["benchmark"] == "unit_price_median"), -x["potential_saving_to_median_gbp"]))
        return deduped
    return results


def find_price_outliers(contracts: list[dict]) -> list[dict]:
    return _price_outlier_analysis(contracts, dedupe=True)


def find_renewal_risks(contracts: list[dict], as_of: date = AS_OF) -> list[dict]:
    """Flag contracts using explicit rules:
    - expired: days_to_end < 0
    - notice_missed: days_past_deadline > 0 and auto_renew == No
    - auto_renew_imminent: days_past_deadline > 0 and auto_renew == Yes
    - renewal_soon: 0 < days_to_end <= LOOK_AHEAD_DAYS and not past deadline
    """
    results = []
    for c in contracts:
        end = c["end_date_dt"]
        notice = c["notice_days_int"]
        deadline = end - timedelta(days=notice)
        days_to_end = (end - as_of).days
        days_past_deadline = (as_of - deadline).days

        status = "ok"
        if days_to_end < 0:
            status = "expired"
        elif days_past_deadline > 0:
            status = "notice_missed" if c["auto_renew"] == "No" else "auto_renew_imminent"
        elif days_to_end <= LOOK_AHEAD_DAYS:
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
                "look_ahead_days": LOOK_AHEAD_DAYS,
                "status": status,
                "annual_spend_gbp": round(c["_annual_spend_gbp"], 2),
                "source": f"contract {c['contract_id']} ({c['evidence_file']})",
            })
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
    """Flag individual invoices where:
    deviation from contract mean > 15% OR deviation from expected monthly (annual/12) > 20%.
    """
    THRESHOLD_MEAN = 0.15
    THRESHOLD_EXPECTED = 0.20
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
            if dev > THRESHOLD_MEAN or dev_expected > THRESHOLD_EXPECTED:
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
                    "threshold_mean_pct": round(THRESHOLD_MEAN * 100, 1),
                    "threshold_expected_pct": round(THRESHOLD_EXPECTED * 100, 1),
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

    # Duplicate values
    duplicate_total = sum(d["total_amount_gbp"] for d in dupes)
    duplicate_additional = sum(d["additional_duplicate_value_gbp"] for d in dupes)

    # Resubmitted: in this dataset every resubmitted belongs to a duplicate group,
    # so the exposure is the same as duplicate_additional.  We keep both for transparency.
    resubmitted_exposure = sum(r["amount_gbp"] for r in resubmitted)

    unmapped_exposure = sum(u["amount_gbp"] for u in unmapped)

    # Savings benchmarks (three views for transparency)
    all_outliers = _price_outlier_analysis(contracts, dedupe=False)
    all_annual = [o for o in all_outliers if o["benchmark"] == "annual_spend_median"]
    all_unit   = [o for o in all_outliers if o["benchmark"] == "unit_price_median"]
    potential_consolidation_annual_all = sum(o["potential_saving_to_median_gbp"] for o in all_annual)
    potential_consolidation_unit_all   = sum(o["potential_saving_to_median_gbp"] for o in all_unit)

    a_ids = {o["contract_id"] for o in all_annual}
    u_ids = {o["contract_id"] for o in all_unit}
    vol_only = a_ids - u_ids
    price_only = u_ids - a_ids
    both = a_ids & u_ids
    vol_only_saving = sum(o["potential_saving_to_median_gbp"] for o in all_annual if o["contract_id"] in vol_only)
    price_only_saving = sum(o["potential_saving_to_median_gbp"] for o in all_unit if o["contract_id"] in price_only)
    both_annual_saving = sum(o["potential_saving_to_median_gbp"] for o in all_annual if o["contract_id"] in both)
    both_unit_saving = sum(o["potential_saving_to_median_gbp"] for o in all_unit if o["contract_id"] in both)

    # Invoice anomaly exposure headline = unmapped + additional duplicates + any standalone resubmitted
    # In this dataset, resubmitted are all inside duplicate groups, so:
    #   headline_exposure = unmapped + duplicate_additional
    # But the total combined record value (duplicate_total + unmapped) is higher;
    # present both transparently.
    headline_exposure = unmapped_exposure + duplicate_additional
    total_combined_exposure = unmapped_exposure + duplicate_total

    # Discrepancy counts: avoid double-counting.
    # Confirmed = duplicate groups + unmapped invoices (hard evidence in data).
    # Potential = resubmitted invoices (need manual review to confirm duplicate payment).
    # Note: resubmitted records here are subsets of duplicate groups, so they do not
    # increment the confirmed count.
    confirmed_discrepancies = len(dupes) + len(unmapped)
    potential_recoveries = len(dupes)  # each duplicate group has an extra record

    return {
        "as_of": str(AS_OF),
        "contract_count": len(contracts),
        "invoice_count": len(invoices),
        "total_annual_contract_spend_gbp": round(total_annual_spend, 2),
        "total_invoiced_jan_jun_gbp": round(total_invoiced, 2),
        "upcoming_renewal_count": len(renewals),
        "renewal_breakdown": {
            "expired": sum(1 for r in renewals if r["status"] == "expired"),
            "notice_missed": sum(1 for r in renewals if r["status"] == "notice_missed"),
            "auto_renew_imminent": sum(1 for r in renewals if r["status"] == "auto_renew_imminent"),
            "renewal_soon": sum(1 for r in renewals if r["status"] == "renewal_soon"),
        },
        "duplicate_invoice_total_gbp": round(duplicate_total, 2),
        "duplicate_invoice_additional_gbp": round(duplicate_additional, 2),
        "unmapped_invoice_exposure_gbp": round(unmapped_exposure, 2),
        "resubmitted_invoice_exposure_gbp": round(resubmitted_exposure, 2),
        "invoice_anomaly_headline_exposure_gbp": round(headline_exposure, 2),
        "invoice_anomaly_total_combined_gbp": round(total_combined_exposure, 2),
        "invoice_variance_flags": len(variance),
        "potential_consolidation_savings_annual_median_all_gbp": round(potential_consolidation_annual_all, 2),
        "potential_consolidation_savings_unit_median_all_gbp": round(potential_consolidation_unit_all, 2),
        "savings_contracts_annual_median_all_count": len(a_ids),
        "savings_contracts_unit_median_all_count": len(u_ids),
        "savings_volume_only_count": len(vol_only),
        "savings_volume_only_gbp": round(vol_only_saving, 2),
        "savings_price_only_count": len(price_only),
        "savings_price_only_gbp": round(price_only_saving, 2),
        "savings_both_annual_count": len(both),
        "savings_both_annual_gbp": round(both_annual_saving, 2),
        "savings_both_unit_gbp": round(both_unit_saving, 2),
        "confirmed_discrepancies": confirmed_discrepancies,
        "potential_recoveries": potential_recoveries,
    }


def all_findings(contracts: list[dict], invoices: list[dict]) -> list[dict]:
    """Ranked union of every finding for dashboard consumption.
    De-duplicate: a resubmitted invoice that is also part of a duplicate group
    is surfaced in the duplicate group finding, not separately.
    """
    dupes = find_duplicate_invoice_ids(invoices)
    resubmitted = find_resubmitted_invoices(invoices)
    resub_ids = {r["invoice_id"] for r in resubmitted}

    out = []
    for f in dupes:
        f["severity"] = "confirmed"
        f["financial_value_gbp"] = f["additional_duplicate_value_gbp"]
        f["title"] = f"Duplicate invoice ID {f['invoice_id']} ({f['occurrences']} occurrences, extra = GBP {f['additional_duplicate_value_gbp']:,.2f})"
        out.append(f)

    for f in find_unmapped_invoices(invoices):
        f["severity"] = "confirmed"
        f["financial_value_gbp"] = f["amount_gbp"]
        f["title"] = f"Unmapped invoice {f['invoice_id']} — {f['supplier_canonical']}"
        out.append(f)

    for f in resubmitted:
        if f["invoice_id"] in resub_ids and any(f["invoice_id"] == d["invoice_id"] for d in dupes):
            continue  # already covered by duplicate finding
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
        if f["benchmark"] == "unit_price_median":
            f["title"] = f"Savings opportunity {f['contract_id']} ({f['service_code']}) unit-price > median by GBP {f['potential_saving_to_median_gbp']:,.2f}"
        else:
            f["title"] = f"Savings opportunity {f['contract_id']} ({f['service_code']}) annual-spend > median by GBP {f['potential_saving_to_median_gbp']:,.2f}"
        out.append(f)

    out.sort(key=lambda x: (-{"confirmed": 3, "potential": 2, "risk": 1, "opportunity": 0}[x["severity"]], x["financial_value_gbp"]), reverse=True)
    return out
