from __future__ import annotations
import csv
import io
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session
from app.models import Lead, CRMStatusEvent, DeliveryStatusEvent
from app.services.utils import parse_bool, parse_dt, stable_row_hash
from app.services.sla import upsert_sla_metric

TARGET_COLS = [
    "lead_id", "sale_date", "lead_created_at", "sale_ts",
    "lead_Дата перехода в Сборку", "handed_to_delivery_ts",
    "lead_Дата перехода Передан в доставку", "issued_or_pvz_ts",
    "received_ts", "rejected_ts", "returned_ts", "closed_ts",
    "lead_pipeline_id", "current_status_id", "lead_responsible_user_id",
    "lead_Ответственный за доставку", "lifecycle_incomplete", "buyout_flag",
    "outcome_unknown", "lead_group_id", "lead_group", "contact_Город",
    "lead_Служба доставки", "lead_Метод доставки", "lead_Квалификация лида",
    "lead_Вид оплаты", "lead_source", "lead_Источник", "lead_Тариф Доставки",
    "lead_loss_reason_id",
]

def normalize_cols(cols):
    return [str(c).strip().strip('"').replace("\ufeff", "") for c in cols]

def parse_external_multiline_csv(path: str) -> pd.DataFrame:
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    parts = text.split(";;;")
    header_chunk = parts[0].strip()
    record_starts = [i for i, p in enumerate(parts) if p.strip().startswith('"LEAD_') or p.strip().startswith("LEAD_")]
    if not record_starts:
        raise ValueError("Не удалось найти записи LEAD_")

    def make_csv_line(raw: str) -> str:
        raw = raw.replace("\r", " ").replace("\n", " ")
        raw = raw.replace('""', '"')
        raw = raw.rstrip('"').strip()
        if raw.startswith('"'):
            raw = raw[1:]
        return raw

    header = next(csv.reader(io.StringIO(make_csv_line(header_chunk))))
    header = normalize_cols(header)

    records = []
    for idx, start in enumerate(record_starts):
        end = record_starts[idx + 1] if idx + 1 < len(record_starts) else len(parts)
        row = next(csv.reader(io.StringIO(make_csv_line(";;;".join(parts[start:end])))))
        if len(row) < len(header):
            row += [""] * (len(header) - len(row))
        elif len(row) > len(header):
            row = row[:len(header)]
        records.append(row)

    return pd.DataFrame(records, columns=header)

def read_csv_any(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return parse_external_multiline_csv(path)

def ensure_cols(df: pd.DataFrame):
    for col in TARGET_COLS:
        if col not in df.columns:
            df[col] = pd.NA
    return df

def cross_check_duplicate_fields(row: dict) -> dict:
    issues = []
    ts1 = parse_dt(row.get("handed_to_delivery_ts"))
    ts2 = parse_dt(row.get("lead_Дата перехода Передан в доставку"))
    if ts1 and ts2 and ts1 != ts2:
        issues.append("handed_to_delivery_timestamp_mismatch")
    row["_dq_issues"] = ",".join(issues) if issues else None
    return row

def build_lead_payload(row: dict, source_name: str) -> dict:
    return {
        "lead_id": str(row.get("lead_id")).strip(),
        "sale_date": parse_dt(row.get("sale_date")),
        "lead_created_at": parse_dt(row.get("lead_created_at")),
        "sale_ts": parse_dt(row.get("sale_ts")),
        "assembly_ts": parse_dt(row.get("lead_Дата перехода в Сборку")),
        "handed_to_delivery_ts": parse_dt(row.get("handed_to_delivery_ts")),
        "handed_to_delivery_ts_dup": parse_dt(row.get("lead_Дата перехода Передан в доставку")),
        "issued_or_pvz_ts": parse_dt(row.get("issued_or_pvz_ts")),
        "received_ts": parse_dt(row.get("received_ts")),
        "rejected_ts": parse_dt(row.get("rejected_ts")),
        "returned_ts": parse_dt(row.get("returned_ts")),
        "closed_ts": parse_dt(row.get("closed_ts")),
        "lifecycle_incomplete": parse_bool(row.get("lifecycle_incomplete")),
        "buyout_flag": parse_bool(row.get("buyout_flag")),
        "outcome_unknown": parse_bool(row.get("outcome_unknown")),
        "lead_pipeline_id": None if pd.isna(row.get("lead_pipeline_id")) else str(row.get("lead_pipeline_id")),
        "current_status_id": None if pd.isna(row.get("current_status_id")) else str(row.get("current_status_id")),
        "manager_id": None if pd.isna(row.get("lead_responsible_user_id")) else str(row.get("lead_responsible_user_id")),
        "delivery_manager_id": None if pd.isna(row.get("lead_Ответственный за доставку")) else str(row.get("lead_Ответственный за доставку")),
        "manager_group_id": None if pd.isna(row.get("lead_group_id")) else str(row.get("lead_group_id")),
        "manager_group": None if pd.isna(row.get("lead_group")) else str(row.get("lead_group")),
        "region": None if pd.isna(row.get("contact_Город")) else str(row.get("contact_Город")),
        "delivery_service": None if pd.isna(row.get("lead_Служба доставки")) else str(row.get("lead_Служба доставки")),
        "delivery_method": None if pd.isna(row.get("lead_Метод доставки")) else str(row.get("lead_Метод доставки")),
        "delivery_tariff": None if pd.isna(row.get("lead_Тариф Доставки")) else str(row.get("lead_Тариф Доставки")),
        "payment_type": None if pd.isna(row.get("lead_Вид оплаты")) else str(row.get("lead_Вид оплаты")),
        "lead_qualification": None if pd.isna(row.get("lead_Квалификация лида")) else str(row.get("lead_Квалификация лида")),
        "rejection_category": None if pd.isna(row.get("lead_loss_reason_id")) else str(row.get("lead_loss_reason_id")),
        "lead_source": None if pd.isna(row.get("lead_source")) else str(row.get("lead_source")),
        "lead_source_alt": None if pd.isna(row.get("lead_Источник")) else str(row.get("lead_Источник")),
        "source_dataset": source_name,
        "source_hash": stable_row_hash(row),
    }

def rebuild_events(db: Session, lead: Lead):
    db.query(CRMStatusEvent).filter(CRMStatusEvent.lead_id == lead.lead_id).delete()
    db.query(DeliveryStatusEvent).filter(DeliveryStatusEvent.lead_id == lead.lead_id).delete()

    crm = [
        ("lead_created", lead.lead_created_at),
        ("sale", lead.sale_ts),
        ("assembly", lead.assembly_ts),
    ]
    delivery = [
        ("handed_to_delivery", lead.handed_to_delivery_ts),
        ("issued_or_pvz", lead.issued_or_pvz_ts),
        ("received", lead.received_ts),
        ("rejected", lead.rejected_ts),
        ("returned", lead.returned_ts),
        ("closed", lead.closed_ts),
    ]

    for name, ts in crm:
        if ts:
            db.add(CRMStatusEvent(lead_id=lead.lead_id, status_name=name, status_ts=ts))
    for name, ts in delivery:
        if ts:
            db.add(DeliveryStatusEvent(lead_id=lead.lead_id, status_name=name, status_ts=ts))

def upsert_lead(db: Session, payload: dict) -> Lead:
    lead = db.get(Lead, payload["lead_id"])
    if lead is None:
        lead = Lead(**payload)
        db.add(lead)
        db.flush()
    else:
        for k, v in payload.items():
            setattr(lead, k, v)
        db.flush()
    rebuild_events(db, lead)
    upsert_sla_metric(db, lead)
    return lead

def load_csv_to_db(db: Session, csv_path: str, source_name: str):
    df = read_csv_any(csv_path)
    df.columns = normalize_cols(df.columns)
    df = ensure_cols(df)

    loaded = 0
    for row in df.to_dict(orient="records"):
        row = cross_check_duplicate_fields(row)
        payload = build_lead_payload(row, source_name=source_name)
        if not payload["lead_id"] or payload["lead_id"] == "nan":
            continue
        upsert_lead(db, payload)
        loaded += 1
    db.commit()
    return {"loaded_rows": loaded}
