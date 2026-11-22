from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import select

from app.core.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.models.operational import PatientEncounter
from app.modules.analytics.service import AnalyticsService
from app.modules.analytics.services.staffing_service import StaffingAnalyticsService
from app.modules.analytics.services.financial_service import FinancialAnalyticsService
from app.modules.analytics.services.ed_service import EDAnalyticsService
from app.modules.analytics.services.quality_service import QualityAnalyticsService
from app.modules.data.profiler import DataProfiler

router = APIRouter(prefix="/analytics", tags=["Operational Analytics"])

@router.get("/kpis")
async def get_kpis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Fetch top-line hospital operational KPIs."""
    return await AnalyticsService.get_kpis(db)

@router.get("/scorecards")
async def get_department_scorecards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Fetch department operational scorecards."""
    return await AnalyticsService.get_department_scorecards(db)

@router.get("/staffing")
async def get_staffing_analytics(
    department: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Fetch staffing intelligence, nurse ratios, fill rates, and shift metrics."""
    return await StaffingAnalyticsService.get_staffing_overview(db, department=department)

@router.post("/staffing/simulate")
async def simulate_staffing_ratio(
    current_patients: int = Query(..., ge=1),
    target_ratio: float = Query(..., gt=0.0),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Simulate nurse staffing requirements for given volume and safety ratio target."""
    return await StaffingAnalyticsService.optimize_ratio_simulation(current_patients, target_ratio)

@router.get("/financial")
async def get_financial_analytics(
    department: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Fetch financial operational metrics, cost-per-case, margin analysis, and payer mix."""
    return await FinancialAnalyticsService.get_financial_overview(db, department=department)

@router.get("/ed-flow")
async def get_ed_flow_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Fetch Emergency Department throughput, wait times, triage ESI levels, and disposition metrics."""
    return await EDAnalyticsService.get_ed_overview(db)

@router.get("/quality")
async def get_quality_analytics(
    department: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Fetch 30-day readmission analytics, quality safety events, and clinical compliance scores."""
    return await QualityAnalyticsService.get_quality_overview(db, department=department)

@router.get("/data-health")
async def get_data_health_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Run Data Profiler health check on primary Patient Encounters table."""
    res = await db.execute(select(PatientEncounter).limit(500))
    encs = res.scalars().all()
    if not encs:
        return {
            "health_score": 95.0,
            "status": "excellent",
            "total_rows": 0,
            "summary": "No operational encounters in database yet."
        }

    data = [
        {
            "id": str(e.id),
            "patient_id": e.patient_id,
            "department": e.department,
            "diagnosis_group": e.diagnosis_group,
            "admission_type": e.admission_type,
            "los_days": e.los_days,
            "age": e.age,
            "readmitted_30d": e.readmitted_30d,
            "total_cost": e.total_cost,
            "payer_type": e.payer_type
        }
        for e in encs
    ]
    df = pd.DataFrame(data)
    return DataProfiler.profile_dataframe(df, dataset_name="PatientEncounters (Live Sample)")
