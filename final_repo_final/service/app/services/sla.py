from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Lead, SLAMetric
from app.services.norms import load_norms

def duration_days(start: datetime | None, end: datetime | None):
    if not start or not end:
        return None
    return (end - start).total_seconds() / 86400.0

def duration_hours(start: datetime | None, end: datetime | None):
    if not start or not end:
        return None
    return (end - start).total_seconds() / 3600.0

def get_outcome_ts(lead: Lead):
    # earliest known terminal timestamp
    terminals = [lead.received_ts, lead.rejected_ts, lead.returned_ts, lead.closed_ts]
    terminals = [t for t in terminals if t is not None]
    return min(terminals) if terminals else None

def apply_exclusion_rules(lead: Lead) -> tuple[bool, str | None]:
    cfg = load_norms()
    rules = cfg["rules"]

    if rules.get("exclude_lifecycle_incomplete", True) and bool(lead.lifecycle_incomplete):
        return True, "lifecycle_incomplete"

    if rules.get("exclude_outcome_unknown", True) and bool(lead.outcome_unknown):
        return True, "outcome_unknown"

    outcome_ts = get_outcome_ts(lead)
    total_cycle_days = duration_days(lead.sale_ts, outcome_ts)

    checks = [
        duration_hours(lead.sale_ts, lead.handed_to_delivery_ts),
        duration_days(lead.handed_to_delivery_ts, lead.issued_or_pvz_ts),
        duration_days(lead.issued_or_pvz_ts, outcome_ts),
        total_cycle_days,
    ]
    if rules.get("exclude_negative_durations", True):
        if any(v is not None and v < 0 for v in checks):
            return True, "negative_duration"

    max_total = rules.get("exclude_total_cycle_over_days", 60)
    if total_cycle_days is not None and total_cycle_days > max_total:
        return True, f"total_cycle_over_{max_total}_days"

    return False, None

def compute_sla_for_lead(lead: Lead) -> dict:
    cfg = load_norms()["b2c"]
    outcome_ts = get_outcome_ts(lead)

    sla_1 = duration_hours(lead.sale_ts, lead.handed_to_delivery_ts)
    sla_2 = duration_days(lead.handed_to_delivery_ts, lead.issued_or_pvz_ts)
    sla_3 = duration_days(lead.issued_or_pvz_ts, outcome_ts)
    total_cycle = duration_days(lead.sale_ts, outcome_ts)

    excluded, reason = apply_exclusion_rules(lead)

    return {
        "sla_1_sale_to_handover_hours": sla_1,
        "sla_2_handover_to_issue_days": sla_2,
        "sla_3_issue_to_outcome_days": sla_3,
        "total_cycle_days": total_cycle,
        "sla_1_on_time": (sla_1 is not None and sla_1 <= cfg["sla_1_sale_to_handover_hours"]) if not excluded else None,
        "sla_2_on_time": (sla_2 is not None and sla_2 <= cfg["sla_2_handover_to_issue_days"]) if not excluded else None,
        "sla_3_on_time": (sla_3 is not None and sla_3 <= cfg["sla_3_issue_to_outcome_days"]) if not excluded else None,
        "total_cycle_on_time": (total_cycle is not None and total_cycle <= cfg["total_cycle_days"]) if not excluded else None,
        "is_excluded": excluded,
        "exclusion_reason": reason,
    }

def upsert_sla_metric(db: Session, lead: Lead):
    values = compute_sla_for_lead(lead)
    metric = db.query(SLAMetric).filter(SLAMetric.lead_id == lead.lead_id).one_or_none()
    if metric is None:
        metric = SLAMetric(lead_id=lead.lead_id, **values)
        db.add(metric)
    else:
        for k, v in values.items():
            setattr(metric, k, v)
    return metric

def recompute_all_sla(db: Session):
    leads = db.query(Lead).all()
    for lead in leads:
        upsert_sla_metric(db, lead)
    db.commit()
