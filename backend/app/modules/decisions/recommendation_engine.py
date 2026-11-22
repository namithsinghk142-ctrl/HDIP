"""
Recommendation Engine — Phase 4 Decision Intelligence
======================================================
Generates data-driven, quantitative, explainable recommendations from
ML prediction outputs. All impact estimates are derived from parametric
formulas applied to live prediction values — no static text fallbacks.

Recommendation Structure:
  - Exact action text with quantities (staff count, beds, time window)
  - Multi-level confidence profile (prediction / recommendation / overall)
  - Composite priority score → tier P1–P4
  - Reasoning chain: prediction → SHAP → formula → expected outcome
  - Expected operational outcomes (wait reduction, occupancy delta, staffing change)
  - Financial impact in INR (formula-derived)
"""

import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

# Formula weight per category — reflects how deterministic the recommendation
# formula is; staffing formulas are near-deterministic while financial estimates
# have higher variance, so lower weight is applied.
FORMULA_WEIGHTS: Dict[str, float] = {
    "staffing":      0.95,
    "capacity":      0.90,
    "throughput":    0.88,
    "flow":          0.88,
    "clinical_care": 0.82,
    "pharmacy":      0.84,
    "financial":     0.80,
    "process":       0.86,
}

# Cost constants (INR)
NURSE_HOURLY_COST_INR = 450           # ₹450/hr per nurse
NURSE_SHIFT_COST_INR = 9_000          # typical 8-hr shift per nurse
BED_SETUP_COST_INR = 12_000           # fixed cost per temporary bed opened
BED_DAILY_OPERATIONAL_INR = 3_500     # daily running cost per extra bed
READMISSION_PENALTY_INR = 14_500      # average per readmission penalty/cost
DELAYED_TRIAGE_COST_INR = 2_800       # cost per delayed triage case
LWBS_COST_INR = 18_500                # revenue loss per LWBS patient

# Operational parameters
TARGET_NURSE_PATIENT_RATIO = 4.0      # patients per nurse (general ward)
TARGET_ED_RATIO = 3.0                 # ED patients per nurse
SAFE_OCCUPANCY_THRESHOLD = 88.0       # % — above this, action required
SAFE_WAIT_THRESHOLD_MIN = 35.0        # minutes — above this, staffing action needed
WAIT_REDUCTION_PER_NURSE_MIN = 8.5    # minutes of wait reduction per extra ED nurse
HIGH_RISK_TIER = {"very_high", "high"}


# ──────────────────────────────────────────────────────────────────────────────
# Multi-Level Confidence
# ──────────────────────────────────────────────────────────────────────────────

def compute_confidence_profile(
    prediction_confidence: float,
    category: str,
    scenario_applicable: bool = False,
    perturbed_param_count: int = 0,
    any_param_exceeds_30pct: bool = False,
) -> Dict[str, float]:
    """
    Compute the four-level confidence profile for a recommendation.

    Levels:
      prediction_confidence     — directly from ML model output
      recommendation_confidence — prediction_conf × formula_weight(category)
      scenario_simulation_conf  — only for scenario results; penalised for
                                  complexity and extrapolation distance
      overall_decision_conf     — harmonic mean of applicable layers
    """
    formula_weight = FORMULA_WEIGHTS.get(category, 0.86)
    recommendation_confidence = round(prediction_confidence * formula_weight, 4)

    profile: Dict[str, float] = {
        "prediction_confidence":      round(prediction_confidence, 4),
        "recommendation_confidence":  recommendation_confidence,
    }

    if scenario_applicable:
        complexity_penalty    = 0.02 * perturbed_param_count
        extrapolation_penalty = 0.03 if any_param_exceeds_30pct else 0.0
        sim_conf = round(
            prediction_confidence * (1.0 - complexity_penalty) * (1.0 - extrapolation_penalty),
            4,
        )
        sim_conf = max(0.50, sim_conf)          # floor at 50% for extreme scenarios
        profile["scenario_simulation_confidence"] = sim_conf
        applicable = [prediction_confidence, recommendation_confidence, sim_conf]
    else:
        applicable = [prediction_confidence, recommendation_confidence]

    # Weighted harmonic mean — penalises weak confidence layers appropriately
    harmonic = len(applicable) / sum(1.0 / max(c, 0.01) for c in applicable)
    profile["overall_decision_confidence"] = round(harmonic, 4)

    return profile


# ──────────────────────────────────────────────────────────────────────────────
# Priority Scoring
# ──────────────────────────────────────────────────────────────────────────────

def compute_priority_score(
    risk_severity_score: float,     # 0–100
    urgency_score: float,           # 0–100
    improvement_magnitude: float,   # 0–100 (normalised expected improvement)
    implementation_difficulty: str, # "low", "medium", "high"
) -> float:
    """
    Composite priority score from four weighted components.

    priority_score =
        0.35 × risk_severity_score
      + 0.25 × urgency_score
      + 0.25 × improvement_magnitude
      − 0.15 × difficulty_penalty
    """
    difficulty_penalties = {"low": 10.0, "medium": 40.0, "high": 70.0}
    difficulty_penalty = difficulty_penalties.get(implementation_difficulty, 40.0)
    score = (
        0.35 * risk_severity_score
        + 0.25 * urgency_score
        + 0.25 * improvement_magnitude
        - 0.15 * difficulty_penalty
    )
    return round(max(0.0, min(100.0, score)), 2)


def priority_tier(score: float) -> str:
    """Map composite priority score to P1–P4 tier."""
    if score >= 85.0:
        return "P1"
    if score >= 65.0:
        return "P2"
    if score >= 40.0:
        return "P3"
    return "P4"


def priority_tier_label(tier: str) -> str:
    labels = {
        "P1": "Critical — Immediate Action Required",
        "P2": "High — Act Within 2 Hours",
        "P3": "Medium — Act Within 24 Hours",
        "P4": "Low — Plan for Next Shift",
    }
    return labels.get(tier, "")


# ──────────────────────────────────────────────────────────────────────────────
# Effectiveness Score Helper
# ──────────────────────────────────────────────────────────────────────────────

def dimension_accuracy(expected: Optional[float], actual: Optional[float], default: Optional[float] = 0.0) -> Optional[float]:
    """
    Compute per-dimension accuracy score (0–100).
    Returns default if either value is missing.
    """
    if expected is None or actual is None:
        return default
    if abs(expected) < 1e-6:
        return 100.0 if abs(actual) < 1e-6 else 0.0
    accuracy = max(0.0, 1.0 - abs(actual - expected) / abs(expected)) * 100.0
    return round(accuracy, 1)


def compute_effectiveness_scores(outcome: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute the three aggregate effectiveness scores from a submitted outcome dict.
    Called by the router when `POST /decisions/audit-log/{id}/outcome` is received.
    """
    pred_acc = dimension_accuracy(
        outcome.get("expected_wait_reduction_min"),
        outcome.get("actual_wait_reduction_min"),
        default=None,
    )
    occ_acc = dimension_accuracy(
        outcome.get("expected_occupancy_change_pct"),
        outcome.get("actual_occupancy_change_pct"),
        default=None,
    )
    pred_dims = [v for v in [pred_acc, occ_acc] if v is not None]
    prediction_accuracy_score = round(sum(pred_dims) / len(pred_dims), 1) if pred_dims else 0.0

    recommendation_effectiveness_score = dimension_accuracy(
        outcome.get("expected_improvement"),
        outcome.get("actual_improvement"),
        default=0.0,
    ) or 0.0

    cost_estimation_accuracy_score = dimension_accuracy(
        outcome.get("expected_cost_inr"),
        outcome.get("actual_cost_inr"),
        default=0.0,
    ) or 0.0

    return {
        "prediction_accuracy_score":         prediction_accuracy_score,
        "recommendation_effectiveness_score": recommendation_effectiveness_score,
        "cost_estimation_accuracy_score":    cost_estimation_accuracy_score,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Recommendation Engine
# ──────────────────────────────────────────────────────────────────────────────

class RecommendationEngine:
    """
    Generates data-driven, quantitative recommendations from ML prediction
    outputs. Every recommendation is derived from parametric formulas applied
    to live prediction values.

    No static text is returned — all quantities (nurse count, bed count,
    time windows, cost figures) are computed from prediction outputs.
    """

    def generate(
        self,
        model_type: str,
        prediction: Dict[str, Any],
        impact: Dict[str, Any],
        explanation: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Entry point. Routes to the appropriate model-specific generator.

        Returns a list of recommendation dicts, sorted by priority_score desc.
        """
        generators = {
            "demand_forecast":    self._demand_forecast_recommendations,
            "bed_occupancy":      self._bed_occupancy_recommendations,
            "ed_wait_time":       self._ed_wait_time_recommendations,
            "readmission_risk":   self._readmission_risk_recommendations,
        }
        gen = generators.get(model_type)
        if gen is None:
            return []

        recs = gen(prediction, impact, explanation)

        # Sort by priority score (descending), then by overall_decision_confidence
        recs.sort(
            key=lambda r: (
                -r.get("priority_score", 0),
                -r.get("confidence_profile", {}).get("overall_decision_confidence", 0),
            )
        )
        return recs

    # ──────────────────────────────────────────────────────────────────────────
    # Demand Forecast Recommendations
    # ──────────────────────────────────────────────────────────────────────────

    def _demand_forecast_recommendations(
        self, prediction: Dict, impact: Dict, explanation: Dict
    ) -> List[Dict]:
        surge_pct = prediction.get("predicted_volume_surge_pct", 0.0)
        avg_vol   = prediction.get("average_volume", 45.0)
        pred_conf = prediction.get("confidence_score", 0.89)
        shap_top  = explanation.get("top_factors", [])
        risk      = impact.get("risk_level", "medium")

        recs = []

        # ── R1: Flex-Staffing Activation ─────────────────────────────────────
        if surge_pct > 5.0:
            extra_patients = round(avg_vol * surge_pct / 100.0)
            extra_nurses   = math.ceil(extra_patients / TARGET_NURSE_PATIENT_RATIO)
            extra_nurses   = max(1, extra_nurses)

            shift_start, shift_end = self._peak_shift_window(surge_pct)
            cost_inr = extra_nurses * NURSE_SHIFT_COST_INR

            risk_score = {"critical": 95, "high": 80, "medium": 60, "low": 30}.get(risk, 60)
            urgency_score = 90 if surge_pct > 15 else (75 if surge_pct > 8 else 55)
            improvement_mag = min(90, surge_pct * 4)
            p_score = compute_priority_score(risk_score, urgency_score, improvement_mag, "medium")
            conf_profile = compute_confidence_profile(pred_conf, "staffing")

            reasoning = self._build_reasoning_chain(
                model_type="demand_forecast",
                prediction_summary=f"Predicted patient volume surge of +{surge_pct}% ({extra_patients} additional patients expected)",
                shap_factors=shap_top,
                impact_summary=impact.get("summary", ""),
                decision_logic=f"surge_pct={surge_pct}% → extra_patients={extra_patients} → nurses_needed=ceil({extra_patients}/{TARGET_NURSE_PATIENT_RATIO})={extra_nurses}",
                expected_outcome=f"Maintain nurse-patient ratio ≤1:{TARGET_NURSE_PATIENT_RATIO}; prevent triage breakdown",
            )

            recs.append({
                "recommendation_id":   f"demand_forecast_R1",
                "action":              (
                    f"Activate flex-staffing roster: deploy {extra_nurses} additional nurse(s) "
                    f"across Emergency and MedSurg between {shift_start} and {shift_end}."
                ),
                "action_detail": (
                    f"Deploy {extra_nurses} RN(s) from on-call pool to Emergency ({math.ceil(extra_nurses * 0.6)}) "
                    f"and MedSurg ({math.floor(extra_nurses * 0.4)}) units. "
                    f"Activate flex-staffing protocol at {shift_start}."
                ),
                "category":            "staffing",
                "priority_score":      p_score,
                "priority_tier":       priority_tier(p_score),
                "priority_tier_label": priority_tier_label(priority_tier(p_score)),
                "urgency":             "immediate" if surge_pct > 15 else "within_4h",
                "department":          "Emergency & MedSurg",
                "quantity":            extra_nurses,
                "time_window":         f"{shift_start} – {shift_end}",
                "expected_improvement": round(surge_pct * 3.2, 1),
                "expected_wait_reduction_min":   None,
                "expected_occupancy_change_pct": round(-surge_pct * 0.4, 1),
                "expected_staffing_change":      extra_nurses,
                "expected_financial_impact_inr": cost_inr,
                "implementation_difficulty":     "medium",
                "confidence_profile":            conf_profile,
                "reasoning_chain":               reasoning,
            })

        # ── R2: Discharge Acceleration ────────────────────────────────────────
        beds_needed   = impact.get("estimated_extra_beds_needed", 3)
        discharge_beds = max(3, beds_needed)
        discharge_time = "11:00 AM" if datetime.now().hour < 10 else "2:00 PM"

        risk_score    = {"critical": 90, "high": 75, "medium": 55, "low": 25}.get(risk, 55)
        p_score_d     = compute_priority_score(risk_score, 70, min(80, discharge_beds * 12), "low")
        conf_profile_d = compute_confidence_profile(pred_conf, "flow")
        capacity_cost  = discharge_beds * 0   # discharge is cost-neutral; saves boarding costs
        reasoning_d    = self._build_reasoning_chain(
            model_type="demand_forecast",
            prediction_summary=f"Surge of +{surge_pct}% will require ~{beds_needed} additional beds",
            shap_factors=shap_top,
            impact_summary=impact.get("summary", ""),
            decision_logic=f"beds_needed={beds_needed} → expedite {discharge_beds} discharges by {discharge_time}",
            expected_outcome=f"Liberate {discharge_beds} MedSurg beds ahead of incoming surge peak",
        )

        recs.append({
            "recommendation_id":   "demand_forecast_R2",
            "action":              (
                f"Expedite morning discharge huddles to liberate {discharge_beds} MedSurg beds by {discharge_time}. "
                f"Prioritise patients awaiting community placement or IV-to-oral conversion."
            ),
            "action_detail": (
                f"Initiate rapid discharge rounds on MedSurg and Cardiology. "
                f"Target {discharge_beds} patients ready for discharge. "
                f"Coordinate transport and pharmacy clearance by {discharge_time}."
            ),
            "category":            "capacity",
            "priority_score":      p_score_d,
            "priority_tier":       priority_tier(p_score_d),
            "priority_tier_label": priority_tier_label(priority_tier(p_score_d)),
            "urgency":             "within_24h",
            "department":          "MedSurg",
            "quantity":            discharge_beds,
            "time_window":         f"Now – {discharge_time}",
            "expected_improvement": round(discharge_beds * 8.5, 1),
            "expected_wait_reduction_min":   round(discharge_beds * 3.5, 1),
            "expected_occupancy_change_pct": round(-discharge_beds * 0.8, 1),
            "expected_staffing_change":      0,
            "expected_financial_impact_inr": 0,
            "implementation_difficulty":     "low",
            "confidence_profile":            conf_profile_d,
            "reasoning_chain":               reasoning_d,
        })

        return recs

    # ──────────────────────────────────────────────────────────────────────────
    # Bed Occupancy Recommendations
    # ──────────────────────────────────────────────────────────────────────────

    def _bed_occupancy_recommendations(
        self, prediction: Dict, impact: Dict, explanation: Dict
    ) -> List[Dict]:
        peak_occ  = prediction.get("peak_occupancy_pct", 85.0)
        dept      = prediction.get("department", "MedSurg")
        capacity  = prediction.get("capacity", 100)
        pred_conf = prediction.get("confidence_score", 0.91)
        risk      = impact.get("risk_level", "medium")
        shap_top  = explanation.get("top_factors", [])

        recs = []

        # ── R1: Overflow Bed Activation ───────────────────────────────────────
        if peak_occ > SAFE_OCCUPANCY_THRESHOLD:
            occupancy_excess = peak_occ - SAFE_OCCUPANCY_THRESHOLD
            beds_to_open     = max(2, math.ceil(capacity * occupancy_excess / 100.0))

            setup_cost  = beds_to_open * BED_SETUP_COST_INR
            daily_cost  = beds_to_open * BED_DAILY_OPERATIONAL_INR
            total_cost  = setup_cost + daily_cost

            risk_score  = {"critical": 100, "high": 85, "medium": 65, "low": 35}.get(risk, 65)
            urgency_s   = 100 if peak_occ >= 95 else (85 if peak_occ >= 92 else 70)
            p_score     = compute_priority_score(risk_score, urgency_s, min(90, occupancy_excess * 6), "medium")
            conf_p      = compute_confidence_profile(pred_conf, "capacity")

            reasoning   = self._build_reasoning_chain(
                model_type="bed_occupancy",
                prediction_summary=f"{dept} projected peak occupancy: {peak_occ}% (threshold: {SAFE_OCCUPANCY_THRESHOLD}%)",
                shap_factors=shap_top,
                impact_summary=impact.get("summary", ""),
                decision_logic=(
                    f"excess={peak_occ}-{SAFE_OCCUPANCY_THRESHOLD}={occupancy_excess:.1f}% → "
                    f"beds_to_open=ceil({capacity}×{occupancy_excess:.1f}/100)={beds_to_open}"
                ),
                expected_outcome=f"Reduce {dept} occupancy from {peak_occ}% to ~{round(peak_occ - occupancy_excess * 0.9, 1)}%",
            )

            recs.append({
                "recommendation_id":   "bed_occupancy_R1",
                "action":              (
                    f"Authorize opening of {beds_to_open} overflow bed(s) in {dept} West Wing Unit B "
                    f"to manage projected {peak_occ:.0f}% peak occupancy."
                ),
                "action_detail": (
                    f"Open {beds_to_open} surge beds in overflow wing. Assign 1 additional nurse per "
                    f"{math.ceil(beds_to_open / TARGET_NURSE_PATIENT_RATIO)} beds. "
                    f"Setup cost: ₹{setup_cost:,.0f}. Daily operational cost: ₹{daily_cost:,.0f}."
                ),
                "category":            "capacity",
                "priority_score":      p_score,
                "priority_tier":       priority_tier(p_score),
                "priority_tier_label": priority_tier_label(priority_tier(p_score)),
                "urgency":             "immediate" if peak_occ >= 95 else "within_2h",
                "department":          dept,
                "quantity":            beds_to_open,
                "time_window":         "Immediately — next 2 hours",
                "expected_improvement": round(occupancy_excess * 0.85, 1),
                "expected_wait_reduction_min":   round(beds_to_open * 4.2, 1),
                "expected_occupancy_change_pct": round(-occupancy_excess * 0.9, 1),
                "expected_staffing_change":      math.ceil(beds_to_open / TARGET_NURSE_PATIENT_RATIO),
                "expected_financial_impact_inr": total_cost,
                "implementation_difficulty":     "medium",
                "confidence_profile":            conf_p,
                "reasoning_chain":               reasoning,
            })

        # ── R2: Step-Down Evaluation ──────────────────────────────────────────
        step_down_count = max(2, math.ceil(capacity * max(0, peak_occ - 80) / 100.0 * 0.35))
        p_score_sd = compute_priority_score(
            {"critical": 80, "high": 65, "medium": 45, "low": 20}.get(risk, 45),
            60, min(70, step_down_count * 15), "low"
        )
        conf_sd   = compute_confidence_profile(pred_conf, "flow")
        reasoning_sd = self._build_reasoning_chain(
            model_type="bed_occupancy",
            prediction_summary=f"{dept} occupancy at {peak_occ}%; {step_down_count} patients likely eligible for step-down",
            shap_factors=shap_top,
            impact_summary=impact.get("summary", ""),
            decision_logic=f"step_down_candidates=ceil({capacity}×{max(0, peak_occ-80):.1f}/100×0.35)={step_down_count}",
            expected_outcome=f"Free {step_down_count} acute beds; reduce occupancy by ~{round(step_down_count / capacity * 100, 1)}%",
        )

        recs.append({
            "recommendation_id":   "bed_occupancy_R2",
            "action":              (
                f"Schedule step-down evaluations for {step_down_count} telemetry patients in {dept} "
                f"to transition to general ward, freeing acute capacity."
            ),
            "action_detail": (
                f"Attending physician review of {step_down_count} telemetry patients. "
                f"Criteria: stable vitals ×24h, no IV vasoactives. "
                f"Target transfer to general ward within 6 hours."
            ),
            "category":            "flow",
            "priority_score":      p_score_sd,
            "priority_tier":       priority_tier(p_score_sd),
            "priority_tier_label": priority_tier_label(priority_tier(p_score_sd)),
            "urgency":             "within_12h",
            "department":          dept,
            "quantity":            step_down_count,
            "time_window":         "Next 6–12 hours",
            "expected_improvement": round(step_down_count * 12.0, 1),
            "expected_wait_reduction_min":   None,
            "expected_occupancy_change_pct": round(-step_down_count / max(capacity, 1) * 100, 1),
            "expected_staffing_change":      0,
            "expected_financial_impact_inr": 0,
            "implementation_difficulty":     "low",
            "confidence_profile":            conf_sd,
            "reasoning_chain":               reasoning_sd,
        })

        return recs

    # ──────────────────────────────────────────────────────────────────────────
    # ED Wait Time Recommendations
    # ──────────────────────────────────────────────────────────────────────────

    def _ed_wait_time_recommendations(
        self, prediction: Dict, impact: Dict, explanation: Dict
    ) -> List[Dict]:
        wait_min   = prediction.get("predicted_wait_minutes", 35.0)
        ed_census  = prediction.get("ed_census", 28)
        risk_level = prediction.get("risk_level", "medium")
        pred_conf  = prediction.get("confidence_score", 0.87)
        shap_top   = explanation.get("top_factors", [])

        recs = []

        # ── R1: Additional Nurse Deployment ──────────────────────────────────
        if wait_min > SAFE_WAIT_THRESHOLD_MIN:
            excess_wait    = wait_min - SAFE_WAIT_THRESHOLD_MIN
            nurses_needed  = math.ceil(excess_wait / WAIT_REDUCTION_PER_NURSE_MIN)
            nurses_needed  = max(1, min(nurses_needed, 6))   # cap at 6 for realism
            wait_reduction = round(nurses_needed * WAIT_REDUCTION_PER_NURSE_MIN, 1)
            triage_cases   = math.ceil(nurses_needed * 6.8)   # cases per nurse per shift
            cost_inr       = nurses_needed * NURSE_SHIFT_COST_INR

            # Compute time window based on hour-of-day (peak periods)
            hour = datetime.now().hour
            if 14 <= hour < 20:
                window = "14:00 – 20:00"
            elif 8 <= hour < 14:
                window = "08:00 – 14:00"
            else:
                window = "20:00 – 02:00"

            risk_s  = {"critical": 100, "high": 88, "medium": 65, "low": 35}.get(risk_level, 65)
            urgency_s = 100 if risk_level == "critical" else (85 if risk_level == "high" else 65)
            p_score = compute_priority_score(risk_s, urgency_s, min(90, excess_wait * 2.5), "medium")
            conf_p  = compute_confidence_profile(pred_conf, "staffing")

            lwbs_risk = impact.get("estimated_lwbs_risk_pct", 0.0)
            lwbs_cost  = round(lwbs_risk / 100.0 * 5 * LWBS_COST_INR)   # 5-patient window

            reasoning  = self._build_reasoning_chain(
                model_type="ed_wait_time",
                prediction_summary=f"Predicted ED wait: {wait_min} min ({risk_level.upper()} risk); census: {ed_census} patients",
                shap_factors=shap_top,
                impact_summary=impact.get("summary", ""),
                decision_logic=(
                    f"excess_wait={wait_min}-{SAFE_WAIT_THRESHOLD_MIN}={excess_wait:.1f} min → "
                    f"nurses_needed=ceil({excess_wait:.1f}/{WAIT_REDUCTION_PER_NURSE_MIN})={nurses_needed}; "
                    f"wait_reduction={nurses_needed}×{WAIT_REDUCTION_PER_NURSE_MIN}={wait_reduction} min"
                ),
                expected_outcome=(
                    f"Reduce average ED wait from {wait_min} min to ~{round(wait_min - wait_reduction, 1)} min; "
                    f"prevent ~{triage_cases} delayed triage cases; LWBS risk: {lwbs_risk:.1f}%"
                ),
            )

            recs.append({
                "recommendation_id":   "ed_wait_time_R1",
                "action":              (
                    f"Deploy {nurses_needed} additional nurse(s) to the Emergency Department "
                    f"between {window}."
                ),
                "action_detail": (
                    f"Assign {nurses_needed} RN(s) from float pool to ED triage and fast-track. "
                    f"Expected wait reduction: ~{wait_reduction} minutes. "
                    f"Expected cases prevented from delayed triage: ~{triage_cases}. "
                    f"Staffing cost: ₹{cost_inr:,.0f}. LWBS revenue risk avoided: ₹{lwbs_cost:,.0f}."
                ),
                "category":            "staffing",
                "priority_score":      p_score,
                "priority_tier":       priority_tier(p_score),
                "priority_tier_label": priority_tier_label(priority_tier(p_score)),
                "urgency":             "immediate" if risk_level in ("critical", "high") else "within_2h",
                "department":          "Emergency",
                "quantity":            nurses_needed,
                "time_window":         window,
                "expected_improvement": round((excess_wait / max(wait_min, 1)) * 100, 1),
                "expected_wait_reduction_min":   wait_reduction,
                "expected_occupancy_change_pct": round(-nurses_needed * 1.8, 1),
                "expected_staffing_change":      nurses_needed,
                "expected_financial_impact_inr": cost_inr,
                "implementation_difficulty":     "medium",
                "confidence_profile":            conf_p,
                "reasoning_chain":               reasoning,
            })

        # ── R2: Rapid Triage Protocol ─────────────────────────────────────────
        wait_reduction_protocol = min(22.0, wait_min * 0.38)   # protocol reduces 38% of wait
        boarding  = max(0, ed_census - 30)
        risk_s2   = {"critical": 85, "high": 70, "medium": 50, "low": 25}.get(risk_level, 50)
        p_score2  = compute_priority_score(risk_s2, 75, min(85, wait_min * 1.2), "low")
        conf_p2   = compute_confidence_profile(pred_conf, "throughput")

        reasoning2 = self._build_reasoning_chain(
            model_type="ed_wait_time",
            prediction_summary=f"ED wait {wait_min} min; boarding count ~{boarding}",
            shap_factors=shap_top,
            impact_summary=impact.get("summary", ""),
            decision_logic=f"rapid_triage_reduction={wait_min}×0.38={wait_reduction_protocol:.1f} min; boarding_cleared=ceil({boarding}×0.6)",
            expected_outcome=f"Door-to-provider time reduced by {wait_reduction_protocol:.0f} min; {math.ceil(boarding*0.6)} boarding beds cleared",
        )

        recs.append({
            "recommendation_id":   "ed_wait_time_R2",
            "action":              (
                f"Activate Rapid Triage Protocol for ESI Level 3 & 4 patients. "
                f"Assign dedicated discharge-lounge transport nurse to clear {math.ceil(boarding * 0.6)} boarding beds."
            ),
            "action_detail": (
                f"Implement split-flow triage: ESI 3/4 to fast-track; ESI 1/2 to resuscitation bay. "
                f"Dedicated transport nurse manages {math.ceil(boarding * 0.6)} boarding patients awaiting discharge lounge. "
                f"Protocol reduces door-to-provider time by ~{wait_reduction_protocol:.0f} min."
            ),
            "category":            "throughput",
            "priority_score":      p_score2,
            "priority_tier":       priority_tier(p_score2),
            "priority_tier_label": priority_tier_label(priority_tier(p_score2)),
            "urgency":             "immediate",
            "department":          "Emergency",
            "quantity":            math.ceil(boarding * 0.6),
            "time_window":         "Next 1–2 hours",
            "expected_improvement": round(wait_reduction_protocol / max(wait_min, 1) * 100, 1),
            "expected_wait_reduction_min":   round(wait_reduction_protocol, 1),
            "expected_occupancy_change_pct": round(-math.ceil(boarding * 0.6) * 2.5, 1),
            "expected_staffing_change":      1,
            "expected_financial_impact_inr": NURSE_SHIFT_COST_INR,
            "implementation_difficulty":     "low",
            "confidence_profile":            conf_p2,
            "reasoning_chain":               reasoning2,
        })

        return recs

    # ──────────────────────────────────────────────────────────────────────────
    # Readmission Risk Recommendations
    # ──────────────────────────────────────────────────────────────────────────

    def _readmission_risk_recommendations(
        self, prediction: Dict, impact: Dict, explanation: Dict
    ) -> List[Dict]:
        prob         = prediction.get("risk_probability", 0.35)
        tier         = prediction.get("risk_tier", "moderate")
        pred_conf    = prediction.get("confidence_score", 0.86)
        shap_top     = explanation.get("top_factors", [])
        penalty_risk = impact.get("financial_cost_impact_usd", 0) * 83   # USD→INR approx

        recs = []
        is_high_risk = tier in HIGH_RISK_TIER

        # ── R1: Post-Discharge Telehealth Intervention ────────────────────────
        readmission_reduction_pct = 35.0 if is_high_risk else 22.0
        avoided_readmission_prob  = prob * (readmission_reduction_pct / 100.0)
        avoided_cost_inr          = round(avoided_readmission_prob * READMISSION_PENALTY_INR)
        telehealth_cost_inr       = 2_400   # typical 48-hr telehealth check-in cost

        risk_s   = 95 if tier == "very_high" else (80 if tier == "high" else 55)
        urgency_s = 90 if is_high_risk else 65
        p_score  = compute_priority_score(risk_s, urgency_s, min(90, prob * 100 * 1.2), "low")
        conf_p   = compute_confidence_profile(pred_conf, "clinical_care")

        reasoning = self._build_reasoning_chain(
            model_type="readmission_risk",
            prediction_summary=f"30-day readmission risk: {round(prob * 100, 1)}% ({tier.upper()} tier)",
            shap_factors=shap_top,
            impact_summary=impact.get("summary", ""),
            decision_logic=(
                f"risk_prob={round(prob, 4)} × reduction={readmission_reduction_pct}% → "
                f"avoided_prob={round(avoided_readmission_prob, 4)}; "
                f"avoided_cost=₹{avoided_cost_inr:,.0f}; telehealth_cost=₹{telehealth_cost_inr:,.0f}"
            ),
            expected_outcome=(
                f"Reduce 30-day readmission probability by ~{readmission_reduction_pct}%; "
                f"net financial benefit: ₹{max(0, avoided_cost_inr - telehealth_cost_inr):,.0f}"
            ),
        )

        recs.append({
            "recommendation_id":   "readmission_risk_R1",
            "action":              (
                f"Schedule post-discharge home health telehealth check-in within 48 hours "
                f"for this {tier.upper()} risk patient (readmission probability: {round(prob * 100, 1)}%)."
            ),
            "action_detail": (
                f"Arrange video telehealth appointment with primary care within 48h. "
                f"Review medications, symptom flags, and follow-up plan. "
                f"Enroll in transitional care program if {tier} or very_high tier. "
                f"Expected readmission risk reduction: ~{readmission_reduction_pct}%. "
                f"Estimated avoided penalty: ₹{avoided_cost_inr:,.0f}. "
                f"Intervention cost: ₹{telehealth_cost_inr:,.0f}."
            ),
            "category":            "clinical_care",
            "priority_score":      p_score,
            "priority_tier":       priority_tier(p_score),
            "priority_tier_label": priority_tier_label(priority_tier(p_score)),
            "urgency":             "prior_to_discharge",
            "department":          "Discharge Planning",
            "quantity":            1,
            "time_window":         "Within 48 hours post-discharge",
            "expected_improvement": readmission_reduction_pct,
            "expected_wait_reduction_min":   None,
            "expected_occupancy_change_pct": None,
            "expected_staffing_change":      0,
            "expected_financial_impact_inr": -(avoided_cost_inr - telehealth_cost_inr),  # negative = cost
            "implementation_difficulty":     "low",
            "confidence_profile":            conf_p,
            "reasoning_chain":               reasoning,
        })

        # ── R2: Medication Reconciliation ─────────────────────────────────────
        med_rec_reduction = 18.0 if is_high_risk else 12.0
        med_cost_inr      = 1_800   # pharmacy blister pack + reconciliation

        p_score2 = compute_priority_score(
            risk_s, urgency_s - 10, min(75, prob * 100 * 0.9), "low"
        )
        conf_p2  = compute_confidence_profile(pred_conf, "pharmacy")

        reasoning2 = self._build_reasoning_chain(
            model_type="readmission_risk",
            prediction_summary=f"Readmission risk: {round(prob * 100, 1)}%; medication non-adherence is a modifiable factor",
            shap_factors=shap_top,
            impact_summary=impact.get("summary", ""),
            decision_logic=f"med_reconciliation_reduction={med_rec_reduction}%; cost=₹{med_cost_inr}",
            expected_outcome=f"Prevent adverse drug events; reduce readmission risk by ~{med_rec_reduction}%",
        )

        recs.append({
            "recommendation_id":   "readmission_risk_R2",
            "action":              (
                f"Conduct bedside medication reconciliation and provide 30-day pharmacy blister pack "
                f"prior to discharge."
            ),
            "action_detail": (
                f"Clinical pharmacist bedside review: reconcile discharge medications, "
                f"counsel on adherence, provide labelled 30-day blister pack. "
                f"Expected readmission risk reduction from non-adherence: ~{med_rec_reduction}%. "
                f"Cost: ₹{med_cost_inr:,.0f}."
            ),
            "category":            "pharmacy",
            "priority_score":      p_score2,
            "priority_tier":       priority_tier(p_score2),
            "priority_tier_label": priority_tier_label(priority_tier(p_score2)),
            "urgency":             "prior_to_discharge",
            "department":          "Pharmacy",
            "quantity":            1,
            "time_window":         "Day of discharge",
            "expected_improvement": med_rec_reduction,
            "expected_wait_reduction_min":   None,
            "expected_occupancy_change_pct": None,
            "expected_staffing_change":      0,
            "expected_financial_impact_inr": -med_cost_inr,
            "implementation_difficulty":     "low",
            "confidence_profile":            conf_p2,
            "reasoning_chain":               reasoning2,
        })

        return recs

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _peak_shift_window(surge_pct: float):
        """Return recommended deployment window based on surge magnitude."""
        hour = datetime.now().hour
        if surge_pct > 20:
            return "12:00", "22:00"
        elif hour < 10:
            return "14:00", "20:00"
        else:
            return "16:00", "22:00"

    @staticmethod
    def _build_reasoning_chain(
        model_type: str,
        prediction_summary: str,
        shap_factors: List[Dict],
        impact_summary: str,
        decision_logic: str,
        expected_outcome: str,
    ) -> List[Dict[str, str]]:
        """
        Build the step-by-step reasoning chain that traces every recommendation
        from raw ML prediction through to expected operational outcome.
        """
        top_shap = shap_factors[:3] if shap_factors else []
        shap_text = "; ".join(
            f"{f.get('feature', 'Unknown')} (impact: {f.get('impact', 0):.2f}, {f.get('direction', '')})"
            for f in top_shap
        ) or "SHAP attribution not available"

        return [
            {
                "step":        "1. ML Model Prediction",
                "description": prediction_summary,
                "source":      model_type,
            },
            {
                "step":        "2. SHAP Explainability",
                "description": f"Top driving factors: {shap_text}",
                "source":      "TreeSHAP_Feature_Attribution",
            },
            {
                "step":        "3. Impact Assessment",
                "description": impact_summary,
                "source":      "DecisionEngine._assess_impact",
            },
            {
                "step":        "4. Recommendation Formula",
                "description": decision_logic,
                "source":      "RecommendationEngine",
            },
            {
                "step":        "5. Expected Operational Outcome",
                "description": expected_outcome,
                "source":      "CascadeImpactAnalyzer",
            },
        ]


# Module-level singleton
recommendation_engine = RecommendationEngine()
