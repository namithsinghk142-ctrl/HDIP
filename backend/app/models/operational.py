import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, Date, Boolean, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class PatientEncounter(Base):
    __tablename__ = "patient_encounters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    admit_date: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    discharge_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    department: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    diagnosis_group: Mapped[str] = mapped_column(String(100), nullable=False)
    admission_type: Mapped[str] = mapped_column(String(50), nullable=False) # Emergency, Elective, Urgent
    los_days: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    readmitted_30d: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payer_type: Mapped[str] = mapped_column(String(50), nullable=False) # Medicare, Private, Medicaid, Self

    __table_args__ = (
        Index("idx_encounter_dept_date", "department", "admit_date"),
    )

class BedCensus(Base):
    __tablename__ = "bed_census"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    snapshot_hour: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    department: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    total_beds: Mapped[int] = mapped_column(Integer, nullable=False)
    occupied_beds: Mapped[int] = mapped_column(Integer, nullable=False)
    occupancy_pct: Mapped[float] = mapped_column(Float, nullable=False)
    available_beds: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index("idx_bed_census_dept_date", "department", "snapshot_date"),
    )

class StaffingRecord(Base):
    __tablename__ = "staffing_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shift_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    department: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    shift_type: Mapped[str] = mapped_column(String(20), nullable=False) # Day, Night, Evening
    nurses_scheduled: Mapped[int] = mapped_column(Integer, nullable=False)
    nurses_actual: Mapped[int] = mapped_column(Integer, nullable=False)
    patients_count: Mapped[int] = mapped_column(Integer, nullable=False)
    nurse_patient_ratio: Mapped[float] = mapped_column(Float, nullable=False)

class EDVisit(Base):
    __tablename__ = "ed_visits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    arrival_time: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    triage_level: Mapped[int] = mapped_column(Integer, nullable=False) # 1 (Critical) to 5 (Non-urgent)
    wait_time_min: Mapped[float] = mapped_column(Float, nullable=False)
    treatment_time_min: Mapped[float] = mapped_column(Float, nullable=False)
    disposition: Mapped[str] = mapped_column(String(50), nullable=False) # Admitted, Discharged, Transferred
    department: Mapped[str] = mapped_column(String(100), default="Emergency", nullable=False)

class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    department: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    cost_category: Mapped[str] = mapped_column(String(100), nullable=False) # Staffing, Supplies, Equipment, Overhead
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    revenue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cost_per_case: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

class QualityEvent(Base):
    __tablename__ = "quality_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False) # Infection, Fall, Medication Error, Readmission
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False) # Low, Medium, High, Critical
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
