from sqlalchemy import func, case
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from app.db import get_db
from app.models import Lead, SLAMetric
from app.schemas import SLASummaryResponse

router = APIRouter(prefix="/api/sla", tags=["sla"])

def pct(num, den):
    return None if den == 0 else float(num) / float(den)

@router.get("/b2c/summary", response_model=SLASummaryResponse)
def b2c_summary(db: Session = Depends(get_db)):
    total_leads = db.query(func.count(Lead.lead_id)).scalar() or 0
    included_leads = db.query(func.count(SLAMetric.id)).filter(SLAMetric.is_excluded == False).scalar() or 0
    excluded_leads = db.query(func.count(SLAMetric.id)).filter(SLAMetric.is_excluded == True).scalar() or 0

    sla_1_coverage = db.query(func.count(SLAMetric.id)).filter(
        SLAMetric.is_excluded == False,
        SLAMetric.sla_1_sale_to_handover_hours.isnot(None)
    ).scalar() or 0
    sla_1_ok = db.query(func.count(SLAMetric.id)).filter(
        SLAMetric.is_excluded == False,
        SLAMetric.sla_1_on_time == True
    ).scalar() or 0

    sla_2_coverage = db.query(func.count(SLAMetric.id)).filter(
        SLAMetric.is_excluded == False,
        SLAMetric.sla_2_handover_to_issue_days.isnot(None)
    ).scalar() or 0
    sla_2_ok = db.query(func.count(SLAMetric.id)).filter(
        SLAMetric.is_excluded == False,
        SLAMetric.sla_2_on_time == True
    ).scalar() or 0

    sla_3_coverage = db.query(func.count(SLAMetric.id)).filter(
        SLAMetric.is_excluded == False,
        SLAMetric.sla_3_issue_to_outcome_days.isnot(None)
    ).scalar() or 0
    sla_3_ok = db.query(func.count(SLAMetric.id)).filter(
        SLAMetric.is_excluded == False,
        SLAMetric.sla_3_on_time == True
    ).scalar() or 0

    total_cycle_coverage = db.query(func.count(SLAMetric.id)).filter(
        SLAMetric.is_excluded == False,
        SLAMetric.total_cycle_days.isnot(None)
    ).scalar() or 0
    total_cycle_ok = db.query(func.count(SLAMetric.id)).filter(
        SLAMetric.is_excluded == False,
        SLAMetric.total_cycle_on_time == True
    ).scalar() or 0

    return SLASummaryResponse(
        total_leads=total_leads,
        included_leads=included_leads,
        excluded_leads=excluded_leads,
        sla_1_coverage=sla_1_coverage,
        sla_1_on_time_share=pct(sla_1_ok, sla_1_coverage),
        sla_2_coverage=sla_2_coverage,
        sla_2_on_time_share=pct(sla_2_ok, sla_2_coverage),
        sla_3_coverage=sla_3_coverage,
        sla_3_on_time_share=pct(sla_3_ok, sla_3_coverage),
        total_cycle_coverage=total_cycle_coverage,
        total_cycle_on_time_share=pct(total_cycle_ok, total_cycle_coverage),
    )
