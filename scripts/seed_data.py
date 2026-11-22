import os
import sys
import uuid
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date

# Set seeds for reproducibility
random.seed(42)
np.random.seed(42)

DEPARTMENTS = ["Emergency", "ICU", "MedSurg", "Pediatrics", "Cardiology", "Oncology"]
DIAGNOSES = {
    "Emergency": ["Acute Chest Pain", "Trauma", "Respiratory Distress", "Fever", "Abdominal Pain"],
    "ICU": ["Sepsis", "ARDS", "Cardiogenic Shock", "Severe Trauma", "Post-Op Complication"],
    "MedSurg": ["Pneumonia", "UTI", "Cellulitis", "COPD Exacerbation", "Post-Surgical Care"],
    "Pediatrics": ["Asthma", "Bronchiolitis", "Dehydration", "Viral Fever", "Appendicitis"],
    "Cardiology": ["Heart Failure", "AMI", "Arrhythmia", "Angina", "Hypertensive Crisis"],
    "Oncology": ["Chemotherapy Reaction", "Neutropenic Fever", "Pain Management", "Tumor Resection"]
}
PAYERS = ["Medicare", "Medicaid", "Private Insurance", "Self Pay"]
BED_CAPACITIES = {
    "Emergency": 40,
    "ICU": 25,
    "MedSurg": 120,
    "Pediatrics": 30,
    "Cardiology": 45,
    "Oncology": 35
}

def generate_synthetic_data(output_dir: str, num_days: int = 730):
    os.makedirs(output_dir, exist_ok=True)
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=num_days)

    print(f"Generating synthetic data from {start_date.date()} to {end_date.date()} ({num_days} days)...")

    # 1. Patient Encounters
    encounters = []
    current_dt = start_date
    patient_counter = 10000

    while current_dt < end_date:
        day_of_week = current_dt.weekday()
        month = current_dt.month
        seasonal_mult = 1.25 if month in [12, 1, 2] else (0.9 if month in [6, 7, 8] else 1.0)
        day_mult = 1.15 if day_of_week == 0 else (0.85 if day_of_week in [5, 6] else 1.0)
        
        base_daily_encounters = int(45 * seasonal_mult * day_mult)

        for _ in range(base_daily_encounters):
            patient_counter += 1
            dept = random.choice(DEPARTMENTS)
            diag = random.choice(DIAGNOSES[dept])
            payer = random.choices(PAYERS, weights=[0.4, 0.2, 0.3, 0.1])[0]
            
            if dept == "Pediatrics":
                age = random.randint(1, 17)
            elif dept in ["ICU", "Cardiology"]:
                age = random.randint(50, 88)
            else:
                age = random.randint(18, 85)

            if dept == "ICU":
                los = round(float(np.random.lognormal(mean=1.5, sigma=0.5)) + 1.0, 1)
            elif dept == "MedSurg":
                los = round(float(np.random.lognormal(mean=1.2, sigma=0.4)) + 1.0, 1)
            else:
                los = round(float(np.random.lognormal(mean=0.8, sigma=0.4)) + 0.5, 1)

            admit_time = current_dt + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            discharge_time = admit_time + timedelta(days=los)

            base_cost = 3000 if dept == "MedSurg" else (8000 if dept in ["ICU", "Cardiology"] else 2000)
            total_cost = round(float(base_cost * (los ** 0.75) * random.uniform(0.85, 1.25)), 2)

            readmit_prob = 0.08 + (0.05 if dept in ["ICU", "Cardiology"] else 0.0) + (0.04 if age > 70 else 0.0)
            readmitted_30d = random.random() < readmit_prob

            encounters.append({
                "id": str(uuid.uuid4()),
                "patient_id": f"P-{patient_counter}",
                "admit_date": admit_time.strftime("%Y-%m-%d %H:%M:%S"),
                "discharge_date": discharge_time.strftime("%Y-%m-%d %H:%M:%S"),
                "department": dept,
                "diagnosis_group": diag,
                "admission_type": random.choices(["Emergency", "Elective", "Urgent"], weights=[0.6, 0.3, 0.1])[0],
                "los_days": los,
                "age": age,
                "readmitted_30d": readmitted_30d,
                "total_cost": total_cost,
                "payer_type": payer
            })

        current_dt += timedelta(days=1)

    encounters_df = pd.DataFrame(encounters)
    encounters_path = os.path.join(output_dir, "patient_encounters.csv")
    encounters_df.to_csv(encounters_path, index=False)
    print(f"[OK] Saved {len(encounters_df)} patient encounters to {encounters_path}")

    # 2. Bed Census
    bed_records = []
    current_dt = start_date

    while current_dt < end_date:
        month = current_dt.month
        seasonal_mult = 1.2 if month in [12, 1, 2] else 1.0
        
        for dept, total_beds in BED_CAPACITIES.items():
            base_occ = 0.75 if dept in ["ICU", "MedSurg"] else 0.65
            occ_pct = min(0.98, max(0.40, base_occ * seasonal_mult * random.uniform(0.9, 1.12)))
            occupied = int(total_beds * occ_pct)
            available = total_beds - occupied

            bed_records.append({
                "id": str(uuid.uuid4()),
                "snapshot_date": current_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "snapshot_hour": 12,
                "department": dept,
                "total_beds": total_beds,
                "occupied_beds": occupied,
                "occupancy_pct": round(occ_pct * 100, 1),
                "available_beds": available
            })

        current_dt += timedelta(days=1)

    bed_df = pd.DataFrame(bed_records)
    bed_path = os.path.join(output_dir, "bed_census.csv")
    bed_df.to_csv(bed_path, index=False)
    print(f"[OK] Saved {len(bed_df)} bed census records to {bed_path}")

    # 3. Staffing Records
    staffing_records = []
    current_dt = start_date

    while current_dt < end_date:
        for dept in DEPARTMENTS:
            total_beds = BED_CAPACITIES[dept]
            ratio_target = 2 if dept == "ICU" else (4 if dept == "MedSurg" else 3)
            scheduled = max(2, int((total_beds * 0.75) / ratio_target))
            actual = max(1, scheduled + random.choice([0, 0, 0, -1, 1]))
            patients = int(total_beds * random.uniform(0.6, 0.9))
            actual_ratio = round(patients / actual, 2) if actual > 0 else 0.0

            staffing_records.append({
                "id": str(uuid.uuid4()),
                "shift_date": current_dt.strftime("%Y-%m-%d"),
                "department": dept,
                "shift_type": random.choice(["Day", "Night", "Evening"]),
                "nurses_scheduled": scheduled,
                "nurses_actual": actual,
                "patients_count": patients,
                "nurse_patient_ratio": actual_ratio
            })

        current_dt += timedelta(days=1)

    staffing_df = pd.DataFrame(staffing_records)
    staffing_path = os.path.join(output_dir, "staffing_records.csv")
    staffing_df.to_csv(staffing_path, index=False)
    print(f"[OK] Saved {len(staffing_df)} staffing records to {staffing_path}")

    # 4. ED Visits
    ed_visits = []
    current_dt = start_date

    while current_dt < end_date:
        daily_visits = random.randint(70, 110)
        for _ in range(daily_visits):
            arr_time = current_dt + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            triage = random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.15, 0.45, 0.25, 0.10])[0]
            wait_time = round(float(np.random.exponential(scale=25.0)) + (60 - triage * 10), 1)
            treatment_time = round(float(np.random.exponential(scale=45.0)) + 30, 1)
            disposition = random.choices(["Admitted", "Discharged", "Transferred"], weights=[0.3, 0.65, 0.05])[0]

            ed_visits.append({
                "id": str(uuid.uuid4()),
                "arrival_time": arr_time.strftime("%Y-%m-%d %H:%M:%S"),
                "triage_level": triage,
                "wait_time_min": max(5.0, wait_time),
                "treatment_time_min": max(15.0, treatment_time),
                "disposition": disposition,
                "department": "Emergency"
            })
        current_dt += timedelta(days=1)

    ed_df = pd.DataFrame(ed_visits)
    ed_path = os.path.join(output_dir, "ed_visits.csv")
    ed_df.to_csv(ed_path, index=False)
    print(f"[OK] Saved {len(ed_df)} ED visit records to {ed_path}")

    # 5. Financial Records
    financial_records = []
    current_dt = start_date
    cost_categories = ["Staffing", "Supplies", "Equipment", "Overhead"]

    while current_dt < end_date:
        for dept in DEPARTMENTS:
            for cat in cost_categories:
                base_amt = 12000 if cat == "Staffing" else (5000 if cat == "Supplies" else 3000)
                if dept in ["ICU", "Cardiology"]:
                    base_amt *= 1.5
                amt = round(base_amt * random.uniform(0.85, 1.25), 2)
                rev = round(amt * random.uniform(1.15, 1.45), 2) if cat in ["Staffing", "Supplies"] else round(amt * 0.9, 2)
                cost_per_case = round(amt / random.randint(15, 45), 2)

                financial_records.append({
                    "id": str(uuid.uuid4()),
                    "record_date": current_dt.strftime("%Y-%m-%d"),
                    "department": dept,
                    "cost_category": cat,
                    "amount": amt,
                    "revenue": rev,
                    "cost_per_case": cost_per_case
                })
        current_dt += timedelta(days=7) # Weekly summaries

    fin_df = pd.DataFrame(financial_records)
    fin_path = os.path.join(output_dir, "financial_records.csv")
    fin_df.to_csv(fin_path, index=False)
    print(f"[OK] Saved {len(fin_df)} financial records to {fin_path}")

    # 6. Quality Events
    quality_events = []
    current_dt = start_date
    event_types = ["Infection", "Fall", "Medication Error", "Readmission"]

    while current_dt < end_date:
        if random.random() < 0.35: # Quality event happens every ~3 days
            dept = random.choice(DEPARTMENTS)
            ev_type = random.choice(event_types)
            sev = random.choices(["Low", "Medium", "High", "Critical"], weights=[0.4, 0.35, 0.2, 0.05])[0]

            quality_events.append({
                "id": str(uuid.uuid4()),
                "event_date": current_dt.strftime("%Y-%m-%d"),
                "event_type": ev_type,
                "department": dept,
                "severity": sev,
                "details": f"{ev_type} reported in {dept} during shift."
            })
        current_dt += timedelta(days=1)

    qual_df = pd.DataFrame(quality_events)
    qual_path = os.path.join(output_dir, "quality_events.csv")
    qual_df.to_csv(qual_path, index=False)
    print(f"[OK] Saved {len(qual_df)} quality event records to {qual_path}")

    print("\n[OK] Synthetic Dataset Generation Complete!")

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "synthetic")
    generate_synthetic_data(out_dir)
