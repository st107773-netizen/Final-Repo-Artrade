from pydantic import BaseModel

class SLASummaryResponse(BaseModel):
    total_leads: int
    included_leads: int
    excluded_leads: int
    sla_1_coverage: int
    sla_1_on_time_share: float | None
    sla_2_coverage: int
    sla_2_on_time_share: float | None
    sla_3_coverage: int
    sla_3_on_time_share: float | None
    total_cycle_coverage: int
    total_cycle_on_time_share: float | None
