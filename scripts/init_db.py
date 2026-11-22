import os
import sys
import asyncio
import pandas as pd
import json
from datetime import datetime
from sqlalchemy import select

# Ensure app path in sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.core.database import engine, Base, AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.operational import (
    PatientEncounter, BedCensus, StaffingRecord, EDVisit, FinancialRecord, QualityEvent
)
from app.models.decision import RecommendationTemplate, OperationalAlert
from app.core.security import get_password_hash

RECOMMENDATION_TEMPLATES = [
    {
        "model_type": "demand_forecast",
        "trigger_condition_json": {"field": "predicted_volume_surge_pct", "operator": ">=", "value": 15},
        "action_template": "Pre-allocate {estimated_extra_beds} extra step-down beds and notify nursing pool for weekend surge.",
        "impact_formula": "Prevents ED boarding backlog and maintains wait time under 30 mins",
        "urgency_rule": "within_24h",
        "category": "capacity"
    },
    {
        "model_type": "bed_occupancy",
        "trigger_condition_json": {"field": "occupancy_pct", "operator": ">=", "value": 88},
        "action_template": "Expedite pending discharges in {department} unit and defer non-urgent elective transfers.",
        "impact_formula": "Reduces unit occupancy by 6-8%, restoring buffer capacity",
        "urgency_rule": "immediate",
        "category": "capacity"
    },
    {
        "model_type": "staffing_demand",
        "trigger_condition_json": {"field": "staffing_shortfall", "operator": ">=", "value": 2},
        "action_template": "Call 2 on-call nurses for {shift_type} shift in {department} to maintain safe nurse-to-patient ratios.",
        "impact_formula": "Restores nurse-patient ratio to target 1:{target_ratio}",
        "urgency_rule": "within_24h",
        "category": "staffing"
    }
]

INITIAL_ALERTS = [
    {
        "alert_type": "bed_capacity_warning",
        "severity": "high",
        "title": "MedSurg Unit Occupancy Risk",
        "description": "MedSurg unit projected to reach 92.4% occupancy in the next 24 hours. Emergency triage backlog expected.",
        "context_json": {"unit": "MedSurg", "current_occupancy": 88.5, "projected_occupancy": 92.4},
        "recommendations_json": [
            {"action": "Expedite 3 pending discharges in MedSurg unit", "urgency": "immediate", "category": "capacity"},
            {"action": "Pre-authorize step-down transfer to telemetry", "urgency": "within_24h", "category": "capacity"}
        ],
        "is_acknowledged": False
    },
    {
        "alert_type": "staffing_strain",
        "severity": "critical",
        "title": "ICU Nurse Ratio Deficit",
        "description": "ICU Night shift ratio projected to reach 1:3.2 due to unscheduled call-outs (safety threshold is 1:2.0).",
        "context_json": {"unit": "ICU", "shift": "Night", "current_ratio": 3.2, "target_ratio": 2.0},
        "recommendations_json": [
            {"action": "Deploy 2 float pool nurses to ICU Night shift", "urgency": "immediate", "category": "staffing"},
            {"action": "Authorize 4h voluntary overtime for Evening shift", "urgency": "within_6h", "category": "staffing"}
        ],
        "is_acknowledged": False
    },
    {
        "alert_type": "ed_wait_surge",
        "severity": "medium",
        "title": "Emergency Department Wait Time Surge",
        "description": "ESI Triage Level 3 average wait time exceeded 45 minutes during afternoon arrival peak.",
        "context_json": {"unit": "Emergency", "esi_level": 3, "avg_wait_min": 48.5},
        "recommendations_json": [
            {"action": "Open Fast-Track triage bay B for non-critical cases", "urgency": "within_1h", "category": "process"}
        ],
        "is_acknowledged": False
    }
]

async def init_db():
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Admin User
        result = await session.execute(select(User).where(User.email == "admin@hospital.org"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                email="admin@hospital.org",
                password_hash=get_password_hash("admin123"),
                full_name="Hospital Chief Administrator",
                role=UserRole.ADMIN,
                department="Executive"
            )
            session.add(admin)
            print("[OK] Default admin created (admin@hospital.org / admin123)")

        # 2. Recommendation Templates
        for tmpl in RECOMMENDATION_TEMPLATES:
            res = await session.execute(
                select(RecommendationTemplate).where(RecommendationTemplate.model_type == tmpl["model_type"])
            )
            if not res.scalar_one_or_none():
                rec_obj = RecommendationTemplate(**tmpl)
                session.add(rec_obj)
        print("[OK] Recommendation templates initialized")

        # 3. Operational Alerts
        for alert_data in INITIAL_ALERTS:
            res = await session.execute(
                select(OperationalAlert).where(OperationalAlert.title == alert_data["title"])
            )
            if not res.scalar_one_or_none():
                alert_obj = OperationalAlert(**alert_data)
                session.add(alert_obj)
        print("[OK] Initial Operational Alerts created")

        await session.commit()

    # 4. Load Synthetic Data into DB Fact Tables
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "synthetic")
    encounters_file = os.path.join(data_dir, "patient_encounters.csv")
    bed_file = os.path.join(data_dir, "bed_census.csv")
    staffing_file = os.path.join(data_dir, "staffing_records.csv")
    ed_file = os.path.join(data_dir, "ed_visits.csv")
    fin_file = os.path.join(data_dir, "financial_records.csv")
    qual_file = os.path.join(data_dir, "quality_events.csv")

    async with AsyncSessionLocal() as session:
        # Patient Encounters
        if os.path.exists(encounters_file):
            c1 = await session.execute(select(PatientEncounter.id))
            if len(c1.scalars().all()) == 0:
                df = pd.read_csv(encounters_file)
                objs = [
                    PatientEncounter(
                        patient_id=row['patient_id'],
                        admit_date=datetime.strptime(row['admit_date'], "%Y-%m-%d %H:%M:%S"),
                        discharge_date=datetime.strptime(row['discharge_date'], "%Y-%m-%d %H:%M:%S") if pd.notna(row['discharge_date']) else None,
                        department=row['department'],
                        diagnosis_group=row['diagnosis_group'],
                        admission_type=row['admission_type'],
                        los_days=float(row['los_days']),
                        age=int(row['age']),
                        readmitted_30d=bool(row['readmitted_30d']),
                        total_cost=float(row['total_cost']),
                        payer_type=row['payer_type']
                    )
                    for _, row in df.iterrows()
                ]
                session.add_all(objs)
                await session.commit()
                print(f"[OK] Inserted {len(objs)} PatientEncounters into database")

        # Bed Census
        if os.path.exists(bed_file):
            c2 = await session.execute(select(BedCensus.id))
            if len(c2.scalars().all()) == 0:
                df = pd.read_csv(bed_file)
                objs = [
                    BedCensus(
                        snapshot_date=datetime.strptime(row['snapshot_date'], "%Y-%m-%d %H:%M:%S"),
                        snapshot_hour=int(row['snapshot_hour']),
                        department=row['department'],
                        total_beds=int(row['total_beds']),
                        occupied_beds=int(row['occupied_beds']),
                        occupancy_pct=float(row['occupancy_pct']),
                        available_beds=int(row['available_beds'])
                    )
                    for _, row in df.iterrows()
                ]
                session.add_all(objs)
                await session.commit()
                print(f"[OK] Inserted {len(objs)} BedCensus records into database")

        # Staffing Records
        if os.path.exists(staffing_file):
            c3 = await session.execute(select(StaffingRecord.id))
            if len(c3.scalars().all()) == 0:
                df = pd.read_csv(staffing_file)
                objs = [
                    StaffingRecord(
                        shift_date=datetime.strptime(row['shift_date'], "%Y-%m-%d").date(),
                        department=row['department'],
                        shift_type=row['shift_type'],
                        nurses_scheduled=int(row['nurses_scheduled']),
                        nurses_actual=int(row['nurses_actual']),
                        patients_count=int(row['patients_count']),
                        nurse_patient_ratio=float(row['nurse_patient_ratio'])
                    )
                    for _, row in df.iterrows()
                ]
                session.add_all(objs)
                await session.commit()
                print(f"[OK] Inserted {len(objs)} StaffingRecords into database")

        # ED Visits
        if os.path.exists(ed_file):
            c4 = await session.execute(select(EDVisit.id))
            if len(c4.scalars().all()) == 0:
                df = pd.read_csv(ed_file)
                objs = [
                    EDVisit(
                        arrival_time=datetime.strptime(row['arrival_time'], "%Y-%m-%d %H:%M:%S"),
                        triage_level=int(row['triage_level']),
                        wait_time_min=float(row['wait_time_min']),
                        treatment_time_min=float(row['treatment_time_min']),
                        disposition=row['disposition'],
                        department=row['department']
                    )
                    for _, row in df.iterrows()
                ]
                session.add_all(objs)
                await session.commit()
                print(f"[OK] Inserted {len(objs)} EDVisits into database")

        # Financial Records
        if os.path.exists(fin_file):
            c5 = await session.execute(select(FinancialRecord.id))
            if len(c5.scalars().all()) == 0:
                df = pd.read_csv(fin_file)
                objs = [
                    FinancialRecord(
                        record_date=datetime.strptime(row['record_date'], "%Y-%m-%d").date(),
                        department=row['department'],
                        cost_category=row['cost_category'],
                        amount=float(row['amount']),
                        revenue=float(row['revenue']),
                        cost_per_case=float(row['cost_per_case'])
                    )
                    for _, row in df.iterrows()
                ]
                session.add_all(objs)
                await session.commit()
                print(f"[OK] Inserted {len(objs)} FinancialRecords into database")

        # Quality Events
        if os.path.exists(qual_file):
            c6 = await session.execute(select(QualityEvent.id))
            if len(c6.scalars().all()) == 0:
                df = pd.read_csv(qual_file)
                objs = [
                    QualityEvent(
                        event_date=datetime.strptime(row['event_date'], "%Y-%m-%d").date(),
                        event_type=row['event_type'],
                        department=row['department'],
                        severity=row['severity'],
                        details={"notes": row['details']} if pd.notna(row['details']) else None
                    )
                    for _, row in df.iterrows()
                ]
                session.add_all(objs)
                await session.commit()
                print(f"[OK] Inserted {len(objs)} QualityEvents into database")

    print("\n[OK] Database Initialization Complete!")

if __name__ == "__main__":
    asyncio.run(init_db())
