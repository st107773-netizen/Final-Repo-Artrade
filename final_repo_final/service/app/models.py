from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Float, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class Lead(Base):
    __tablename__ = "leads"

    lead_id: Mapped[str] = mapped_column(String, primary_key=True)
    sale_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lead_created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sale_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    assembly_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    handed_to_delivery_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    handed_to_delivery_ts_dup: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    issued_or_pvz_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    received_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejected_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    returned_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    lifecycle_incomplete: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    buyout_flag: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    outcome_unknown: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    lead_pipeline_id: Mapped[str | None] = mapped_column(String, nullable=True)
    current_status_id: Mapped[str | None] = mapped_column(String, nullable=True)
    manager_id: Mapped[str | None] = mapped_column(String, nullable=True)
    delivery_manager_id: Mapped[str | None] = mapped_column(String, nullable=True)
    manager_group_id: Mapped[str | None] = mapped_column(String, nullable=True)
    manager_group: Mapped[str | None] = mapped_column(String, nullable=True)

    region: Mapped[str | None] = mapped_column(String, nullable=True)
    delivery_service: Mapped[str | None] = mapped_column(String, nullable=True)
    delivery_method: Mapped[str | None] = mapped_column(String, nullable=True)
    delivery_tariff: Mapped[str | None] = mapped_column(String, nullable=True)
    payment_type: Mapped[str | None] = mapped_column(String, nullable=True)
    lead_qualification: Mapped[str | None] = mapped_column(String, nullable=True)
    rejection_category: Mapped[str | None] = mapped_column(String, nullable=True)
    lead_source: Mapped[str | None] = mapped_column(String, nullable=True)
    lead_source_alt: Mapped[str | None] = mapped_column(String, nullable=True)

    source_dataset: Mapped[str | None] = mapped_column(String, nullable=True)
    source_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    loaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    crm_events: Mapped[list["CRMStatusEvent"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    delivery_events: Mapped[list["DeliveryStatusEvent"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    sla_metric: Mapped["SLAMetric | None"] = relationship(back_populates="lead", cascade="all, delete-orphan", uselist=False)

class CRMStatusEvent(Base):
    __tablename__ = "crm_status_events"
    __table_args__ = (UniqueConstraint("lead_id", "status_name", "status_ts", name="uq_crm_event"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.lead_id"))
    status_name: Mapped[str] = mapped_column(String)
    status_ts: Mapped[datetime] = mapped_column(DateTime)

    lead: Mapped["Lead"] = relationship(back_populates="crm_events")

class DeliveryStatusEvent(Base):
    __tablename__ = "delivery_status_events"
    __table_args__ = (UniqueConstraint("lead_id", "status_name", "status_ts", name="uq_delivery_event"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.lead_id"))
    status_name: Mapped[str] = mapped_column(String)
    status_ts: Mapped[datetime] = mapped_column(DateTime)

    lead: Mapped["Lead"] = relationship(back_populates="delivery_events")

class SLAMetric(Base):
    __tablename__ = "sla_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.lead_id"), unique=True)

    sla_1_sale_to_handover_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    sla_2_handover_to_issue_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    sla_3_issue_to_outcome_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_cycle_days: Mapped[float | None] = mapped_column(Float, nullable=True)

    sla_1_on_time: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    sla_2_on_time: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    sla_3_on_time: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    total_cycle_on_time: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    is_excluded: Mapped[bool] = mapped_column(Boolean, default=False)
    exclusion_reason: Mapped[str | None] = mapped_column(String, nullable=True)

    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lead: Mapped["Lead"] = relationship(back_populates="sla_metric")
