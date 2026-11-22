from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.decision import DecisionAuditLog, OperationalAlert
from app.modules.predictions.models.demand_forecast import DemandForecastModel
from app.modules.predictions.models.bed_occupancy import BedOccupancyModel
from app.modules.predictions.models.ed_wait_time import EDWaitTimeModel
from app.modules.predictions.models.readmission_risk import ReadmissionRiskModel
from app.modules.predictions.monitoring import model_monitor
from app.modules.decisions.recommendation_engine import (
    recommendation_engine,
    compute_confidence_profile,
)

class DecisionEngine:
    """The central Decision Intelligence Engine for HDIP.
       Coordinates Predict -> Explain -> Assess Impact -> Action Recommendation pipeline.
    """

    def __init__(self):
        self.models = {
            "demand_forecast": DemandForecastModel(),
            "bed_occupancy": BedOccupancyModel(),
            "ed_wait_time": EDWaitTimeModel(),
            "readmission_risk": ReadmissionRiskModel()
        }

    async def get_decision(self, db: AsyncSession, model_type: str, input_params: Dict[str, Any]) -> Dict[str, Any]:
        if model_type not in self.models:
            raise ValueError(f"Model type '{model_type}' is not supported in Decision Engine.")

        model = self.models[model_type]
        
        # 1. Predict
        prediction = model.predict(input_params)
        
        # 2. Explain
        explanation = model.explain(prediction)

        # 3. Assess Impact
        impact = self._assess_impact(model_type, prediction)

        # 4. Generate Formula-Driven Recommendations
        recommendations = recommendation_engine.generate(model_type, prediction, impact, explanation)

        # 5. Compute Multi-Level Confidence Profile for the primary prediction
        pred_conf = prediction.get("confidence_score", 0.88)
        primary_category = recommendations[0].get("category", "capacity") if recommendations else "capacity"
        confidence_profile = compute_confidence_profile(pred_conf, primary_category)

        # 6. Fetch Model Registry / Monitoring metadata
        health = model_monitor.get_model_health(model_type)
        model_metadata = {
            "model_version": health.get("version", "v1.0.0") if health else "v1.0.0",
            "last_trained": health.get("last_trained", datetime.utcnow().isoformat()) if health else datetime.utcnow().isoformat(),
            "algorithm": health.get("algorithm", prediction.get("algorithm", "Ensemble")) if health else prediction.get("algorithm", "Ensemble"),
            "drift_status": health.get("drift_status", "healthy") if health else "healthy"
        }

        # Record prediction event in monitor
        latency = input_params.get("simulated_latency_ms", 12.5)
        model_monitor.record_prediction(model_type, latency, pred_conf, prediction)

        return {
            "model_type": model_type,
            "model_metadata": model_metadata,
            "confidence_profile": confidence_profile,
            "prediction": prediction,
            "explanation": explanation,
            "impact": impact,
            "recommendations": recommendations
        }

    async def log_decision_action(
        self,
        db: AsyncSession,
        model_type: str,
        recommendation: Dict[str, Any],
        action: str,
        action_note: Optional[str],
        user_id: Optional[uuid.UUID],
        user_name: Optional[str]
    ) -> DecisionAuditLog:
        """Persists accepted/rejected/deferred decisions to the Decision Audit Trail."""
        audit_entry = DecisionAuditLog(
            model_type=model_type,
            category=recommendation.get("category", "general"),
            priority_tier=recommendation.get("priority_tier", "P3"),
            priority_score=recommendation.get("priority_score", 50.0),
            recommendation_text=recommendation.get("action", ""),
            action_detail=recommendation.get("action_detail", ""),
            confidence_profile_json=recommendation.get("confidence_profile", {}),
            expected_outcome_json={
                "expected_improvement": recommendation.get("expected_improvement"),
                "expected_wait_reduction_min": recommendation.get("expected_wait_reduction_min"),
                "expected_occupancy_change_pct": recommendation.get("expected_occupancy_change_pct"),
                "expected_staffing_change": recommendation.get("expected_staffing_change"),
                "expected_cost_inr": recommendation.get("expected_financial_impact_inr"),
            },
            reasoning_chain_json=recommendation.get("reasoning_chain", []),
            action=action,
            action_note=action_note,
            acted_by_id=user_id,
            acted_by_name=user_name,
            status="implemented" if action == "accepted" else "pending",
            implemented_at=datetime.utcnow() if action == "accepted" else None
        )
        db.add(audit_entry)
        await db.commit()
        await db.refresh(audit_entry)
        return audit_entry

    def _assess_impact(self, model_type: str, prediction: Dict[str, Any]) -> Dict[str, Any]:
        if model_type == "demand_forecast":
            surge = prediction.get("predicted_volume_surge_pct", 0.0)
            avg_vol = prediction.get("average_volume", 45.0)
            
            risk_level = "critical" if surge > 20.0 else ("high" if surge > 12.0 else ("medium" if surge > 5.0 else "low"))
            extra_beds_needed = max(0, int((avg_vol - 40) * 0.7))
            cost_impact = int(extra_beds_needed * 1200 * 3) # 3-day projection

            return {
                "risk_level": risk_level,
                "affected_departments": ["Emergency", "ICU", "MedSurg"],
                "estimated_extra_beds_needed": extra_beds_needed,
                "staffing_gap": {"nurses": max(1, int(extra_beds_needed / 3)), "shift": "Weekend Night"},
                "financial_cost_impact_usd": cost_impact,
                "summary": f"Surge of +{surge}% in patient volume will strain Emergency triage and increase bed demand by ~{extra_beds_needed} beds."
            }

        elif model_type == "bed_occupancy":
            peak_occ = prediction.get("peak_occupancy_pct", 85.0)
            dept = prediction.get("department", "MedSurg")
            
            risk_level = "critical" if peak_occ >= 95.0 else ("high" if peak_occ >= 88.0 else "medium")
            cost_impact = int((peak_occ - 80) * 450) if peak_occ > 80 else 0

            return {
                "risk_level": risk_level,
                "department": dept,
                "peak_occupancy_pct": peak_occ,
                "buffer_capacity_beds": max(0, int(prediction.get("capacity", 100) * (1 - peak_occ/100.0))),
                "financial_cost_impact_usd": cost_impact,
                "summary": f"{dept} is projected to reach {peak_occ}% peak occupancy, leaving critical buffer capacity below safety thresholds."
            }

        elif model_type == "ed_wait_time":
            wait_min = prediction.get("predicted_wait_minutes", 35.0)
            census = prediction.get("ed_census", 28)
            risk_level = prediction.get("risk_level", "medium")
            cost_impact = int(wait_min * 180) if wait_min > 45 else 0

            return {
                "risk_level": risk_level,
                "department": "Emergency",
                "predicted_wait_minutes": wait_min,
                "ed_census": census,
                "estimated_lwbs_risk_pct": round(min(25.0, wait_min * 0.15), 1),
                "financial_cost_impact_usd": cost_impact,
                "summary": f"Emergency wait time of {wait_min} min creates a {risk_level.upper()} LWBS (Left Without Being Seen) risk under current census ({census} patients)."
            }

        elif model_type == "readmission_risk":
            prob = prediction.get("risk_probability", 0.35)
            tier = prediction.get("risk_tier", "moderate")
            risk_level = "high" if tier in ["very_high", "high"] else ("medium" if tier == "moderate" else "low")
            penalty_risk_usd = int(prob * 14500)

            return {
                "risk_level": risk_level,
                "readmission_probability_pct": round(prob * 100, 1),
                "risk_tier": tier,
                "financial_cost_impact_usd": penalty_risk_usd,
                "summary": f"Patient classified as {tier.upper()} 30-day readmission risk ({round(prob*100, 1)}% probability). Estimated readmission penalty exposure: ${penalty_risk_usd}."
            }

        return {"risk_level": "low", "summary": "Standard operational conditions expected."}

decision_engine = DecisionEngine()

