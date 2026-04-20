import argparse
import pandas as pd
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Lead
from app.services.sla import compute_sla_for_lead

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    db: Session = SessionLocal()
    try:
        leads = (
            db.query(Lead)
            .filter(Lead.sale_ts.isnot(None), Lead.handed_to_delivery_ts.isnot(None))
            .order_by(Lead.lead_id)
            .limit(args.limit)
            .all()
        )

        rows = []
        for lead in leads:
            calc = compute_sla_for_lead(lead)
            manual_hours = (lead.handed_to_delivery_ts - lead.sale_ts).total_seconds() / 3600.0
            rows.append({
                "lead_id": lead.lead_id,
                "sale_ts": lead.sale_ts,
                "handed_to_delivery_ts": lead.handed_to_delivery_ts,
                "manual_sla_1_hours": round(manual_hours, 3),
                "computed_sla_1_hours": round(calc["sla_1_sale_to_handover_hours"], 3) if calc["sla_1_sale_to_handover_hours"] is not None else None,
                "match": round(manual_hours, 3) == round(calc["sla_1_sale_to_handover_hours"], 3),
                "excluded": calc["is_excluded"],
                "reason": calc["exclusion_reason"],
            })
        print(pd.DataFrame(rows).to_string(index=False))
    finally:
        db.close()

if __name__ == "__main__":
    main()
