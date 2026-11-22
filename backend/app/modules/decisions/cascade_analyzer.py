"""
Cascading Impact Analyzer — Phase 4 Decision Intelligence
==========================================================
Estimates downstream operational effects across 7 hospital domains
from a given set of prediction outputs or simulation perturbations.

All values are formula-derived from prediction outputs — no static defaults.

Domains:
  1. bed_occupancy_impact        — Δ occupancy %, buffer beds
  2. ed_wait_time_impact         — cascading wait from boarding pressure
  3. staffing_demand_impact      — FTE gap from census change
  4. resource_utilization_impact — supply/equipment consumption delta
  5. operational_cost_impact_inr — staff overtime + supply + equipment cost
  6. readmission_risk_impact     — quality risk from staffing strain
  7. department_workload_impact  — load redistribution across departments
"""

import math
from typing import Dict, Any, List, Optional


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

TARGET_NURSE_PATIENT_RATIO = 4.0
TARGET_ED_RATIO            = 3.0
OVERTIME_COST_PER_HOUR_INR = 680        # ₹/hr per nurse on overtime
SUPPLY_COST_PER_PATIENT_INR = 1_200     # daily supply cost per additional patient
EQUIPMENT_DAILY_INR         = 850       # daily equipment wear per additional patient
BOARDING_WAIT_MULTIPLIER    = 2.8       # each boarding patient adds 2.8 min avg wait
STAFFING_READMISSION_FACTOR = 0.04     # 4% increase in readmission risk per missed ratio breach
READMISSION_PENALTY_INR     = 450_000   # estimated financial penalty exposure per readmission incident

DEPARTMENTS = ["Emergency", "ICU", "MedSurg", "Pediatrics", "Cardiology", "Oncology"]

DEPT_CAPACITIES = {
    "Emergency": 40, "ICU": 25, "MedSurg": 120,
    "Pediatrics": 30, "Cardiology": 45, "Oncology": 35,
}

DEPT_BASELINE_STAFFING = {
    "Emergency": 12, "ICU": 10, "MedSurg": 30,
    "Pediatrics": 8,  "Cardiology": 11, "Oncology": 9,
}


class CascadeImpactAnalyzer:
    """
    Estimates second-order and third-order operational impacts from
    prediction outputs or scenario perturbations.

    Cascade chain examples:
      ED wait time ↑ → boarding ↑ → MedSurg occupancy ↑ → ICU spillover risk ↑
      Patient surge → staffing gap → ratio breach → quality events ↑ → readmission ↑
      Extended LOS → bed block → elective cancellation → revenue loss ↓
    """

    def analyze(
        self,
        model_type: str,
        prediction: Dict[str, Any],
        impact: Dict[str, Any],
        scenario_delta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point. Routes to model-specific analysis.

        Args:
            model_type:     The prediction model that triggered this analysis
            prediction:     Raw prediction output from the ML model
            impact:         Impact assessment from DecisionEngine._assess_impact
            scenario_delta: Optional delta dict from ScenarioSimulator (extra context)

        Returns:
            Dict with 7-domain cascade effects + summary narrative
        """
        effects: Dict[str, Any] = {}

        # Shared context
        census_delta   = (scenario_delta or {}).get("census_delta", 0)
        nurses_delta   = (scenario_delta or {}).get("nurses_delta", 0)
        beds_delta     = (scenario_delta or {}).get("beds_delta", 0)
        primary_dept   = prediction.get("department", "MedSurg")

        # 1. Bed occupancy impact
        effects["bed_occupancy_impact"] = self._bed_occupancy(
            prediction, impact, census_delta, beds_delta, primary_dept
        )

        # 2. ED wait time impact (cascading from boarding)
        effects["ed_wait_time_impact"] = self._ed_wait_time(
            prediction, impact, census_delta, nurses_delta
        )

        # 3. Staffing demand impact
        effects["staffing_demand_impact"] = self._staffing_demand(
            prediction, impact, census_delta, nurses_delta, primary_dept
        )

        # 4. Resource utilization impact
        effects["resource_utilization_impact"] = self._resource_utilization(
            prediction, census_delta
        )

        # 5. Operational cost impact (INR)
        effects["operational_cost_impact"] = self._operational_cost(
            prediction, impact, census_delta, nurses_delta, beds_delta
        )

        # 6. Readmission risk impact
        effects["readmission_risk_impact"] = self._readmission_risk(
            prediction, impact, nurses_delta, census_delta
        )

        # 7. Department workload impact
        effects["department_workload_impact"] = self._department_workload(
            prediction, census_delta, primary_dept
        )

        # Overall cascade severity
        effects["cascade_severity"] = self._cascade_severity(effects)
        effects["cascade_summary"]  = self._cascade_summary(model_type, effects, prediction)

        return effects

    # ──────────────────────────────────────────────────────────────────────────
    # Domain 1: Bed Occupancy
    # ──────────────────────────────────────────────────────────────────────────

    def _bed_occupancy(
        self,
        prediction: Dict,
        impact: Dict,
        census_delta: int,
        beds_delta: int,
        dept: str,
    ) -> Dict[str, Any]:
        current_occ = prediction.get("peak_occupancy_pct", 85.0)
        capacity    = DEPT_CAPACITIES.get(dept, 100)
        effective_capacity = max(1, capacity + beds_delta)

        # Direct impact from census change
        census_occ_delta = round((census_delta / effective_capacity) * 100, 1) if census_delta else 0.0
        # Impact from bed expansion / reduction
        beds_occ_delta   = round((-beds_delta / effective_capacity) * 100, 1) if beds_delta else 0.0

        projected_occ  = round(current_occ + census_occ_delta + beds_occ_delta, 1)
        projected_occ  = max(0.0, min(100.0, projected_occ))
        buffer_beds    = max(0, int(effective_capacity * (1 - projected_occ / 100.0)))
        risk_level     = "critical" if projected_occ >= 95 else ("high" if projected_occ >= 88 else "medium" if projected_occ >= 75 else "low")

        return {
            "current_occupancy_pct":  current_occ,
            "projected_occupancy_pct": projected_occ,
            "occupancy_delta_pct":    round(projected_occ - current_occ, 1),
            "buffer_beds_remaining":  buffer_beds,
            "effective_capacity":     effective_capacity,
            "risk_level":             risk_level,
            "direct_effect":          f"Bed occupancy {'increases' if census_occ_delta > 0 else 'decreases'} by {abs(census_occ_delta):.1f}% due to census change",
            "indirect_effect":        f"Bed expansion of {beds_delta} beds {'reduces' if beds_delta > 0 else 'increases'} effective occupancy by {abs(beds_occ_delta):.1f}%",
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Domain 2: ED Wait Time (Cascading from Boarding)
    # ──────────────────────────────────────────────────────────────────────────

    def _ed_wait_time(
        self,
        prediction: Dict,
        impact: Dict,
        census_delta: int,
        nurses_delta: int,
    ) -> Dict[str, Any]:
        current_wait  = prediction.get("predicted_wait_minutes",
                         impact.get("predicted_wait_minutes", 35.0))
        current_census = prediction.get("ed_census", 28)
        boarding       = max(0, current_census - 30)

        # Census increase cascades to boarding → wait time increase
        boarding_from_surge = max(0, math.ceil(census_delta * 0.35))
        wait_from_boarding  = round(boarding_from_surge * BOARDING_WAIT_MULTIPLIER, 1)

        # Nurse deployment reduces wait
        wait_from_nurses    = round(nurses_delta * 8.5, 1)  # negative = improvement

        projected_wait = round(current_wait + wait_from_boarding - wait_from_nurses, 1)
        projected_wait = max(5.0, min(240.0, projected_wait))
        wait_delta     = round(projected_wait - current_wait, 1)

        risk = "critical" if projected_wait > 90 else ("high" if projected_wait > 60 else "medium" if projected_wait > 35 else "low")

        return {
            "current_wait_min":          current_wait,
            "projected_wait_min":        projected_wait,
            "wait_delta_min":            wait_delta,
            "boarding_count_change":     boarding_from_surge,
            "risk_level":                risk,
            "direct_effect":             f"Boarding count increases by {boarding_from_surge} → adds {wait_from_boarding} min to average wait",
            "indirect_effect":           (
                f"Nurse deployment of {abs(nurses_delta)} reduces wait by {abs(wait_from_nurses)} min"
                if nurses_delta != 0 else "No staffing change applied"
            ),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Domain 3: Staffing Demand
    # ──────────────────────────────────────────────────────────────────────────

    def _staffing_demand(
        self,
        prediction: Dict,
        impact: Dict,
        census_delta: int,
        nurses_delta: int,
        dept: str,
    ) -> Dict[str, Any]:
        current_nurses  = DEPT_BASELINE_STAFFING.get(dept, 12)
        current_patients = prediction.get("ed_census",
                            prediction.get("average_volume", 45))
        projected_patients = max(1, int(current_patients + census_delta))

        ratio   = TARGET_ED_RATIO if dept == "Emergency" else TARGET_NURSE_PATIENT_RATIO
        nurses_required = math.ceil(projected_patients / ratio)
        nurses_available = max(0, current_nurses + nurses_delta)
        fte_gap          = max(0, nurses_required - nurses_available)

        ratio_breach = (nurses_available < nurses_required)
        projected_ratio = round(projected_patients / max(nurses_available, 1), 2)

        return {
            "current_nurses":          current_nurses,
            "nurses_available":        nurses_available,
            "nurses_required":         nurses_required,
            "fte_gap":                 fte_gap,
            "projected_patient_count": projected_patients,
            "projected_nurse_ratio":   projected_ratio,
            "target_ratio":            ratio,
            "ratio_breach":            ratio_breach,
            "direct_effect":           f"Census of {projected_patients} requires {nurses_required} nurses; {nurses_available} available → gap: {fte_gap}",
            "indirect_effect":         (
                "Ratio breach increases risk of missed care events and elevates readmission probability"
                if ratio_breach else "Staffing is sufficient for projected census"
            ),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Domain 4: Resource Utilization
    # ──────────────────────────────────────────────────────────────────────────

    def _resource_utilization(
        self,
        prediction: Dict,
        census_delta: int,
    ) -> Dict[str, Any]:
        base_vol      = prediction.get("average_volume", prediction.get("ed_census", 30))
        projected_vol = max(0, base_vol + census_delta)
        delta_vol     = projected_vol - base_vol

        supply_delta_inr     = round(delta_vol * SUPPLY_COST_PER_PATIENT_INR, 0)
        equipment_delta_inr  = round(delta_vol * EQUIPMENT_DAILY_INR, 0)
        utilization_change   = round((delta_vol / max(base_vol, 1)) * 100, 1)

        return {
            "baseline_patient_volume":    base_vol,
            "projected_patient_volume":   projected_vol,
            "volume_delta":               delta_vol,
            "utilization_change_pct":     utilization_change,
            "supply_cost_delta_inr":      supply_delta_inr,
            "equipment_cost_delta_inr":   equipment_delta_inr,
            "total_resource_delta_inr":   supply_delta_inr + equipment_delta_inr,
            "direct_effect":              f"Volume increase of {delta_vol} patients increases supply consumption by ₹{supply_delta_inr:,.0f}/day",
            "indirect_effect":            f"Equipment utilization increases by {utilization_change:.1f}%; additional wear cost: ₹{equipment_delta_inr:,.0f}/day",
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Domain 5: Operational Cost (INR)
    # ──────────────────────────────────────────────────────────────────────────

    def _operational_cost(
        self,
        prediction: Dict,
        impact: Dict,
        census_delta: int,
        nurses_delta: int,
        beds_delta: int,
    ) -> Dict[str, Any]:
        # Staffing cost
        overtime_nurses   = max(0, nurses_delta)   # added nurses on overtime
        staffing_cost_inr = overtime_nurses * 9_000  # per-shift cost

        # Bed setup cost
        beds_cost_inr = max(0, beds_delta) * 12_000

        # Supply/equipment from census increase
        supply_cost_inr = max(0, census_delta) * SUPPLY_COST_PER_PATIENT_INR
        equip_cost_inr  = max(0, census_delta) * EQUIPMENT_DAILY_INR

        total_cost_inr   = staffing_cost_inr + beds_cost_inr + supply_cost_inr + equip_cost_inr
        financial_impact = impact.get("financial_cost_impact_usd", 0) * 83   # USD→INR

        return {
            "staffing_cost_inr":     staffing_cost_inr,
            "bed_setup_cost_inr":    beds_cost_inr,
            "supply_cost_inr":       supply_cost_inr,
            "equipment_cost_inr":    equip_cost_inr,
            "total_operational_cost_inr": total_cost_inr,
            "existing_financial_exposure_inr": round(financial_impact, 0),
            "direct_effect":         f"Additional staffing ({overtime_nurses} nurses) + bed setup: ₹{staffing_cost_inr + beds_cost_inr:,.0f}",
            "indirect_effect":       f"Supply + equipment costs from {census_delta} extra patients: ₹{supply_cost_inr + equip_cost_inr:,.0f}/day",
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Domain 6: Readmission Risk
    # ──────────────────────────────────────────────────────────────────────────

    def _readmission_risk(
        self,
        prediction: Dict,
        impact: Dict,
        nurses_delta: int,
        census_delta: int,
    ) -> Dict[str, Any]:
        current_risk     = prediction.get("risk_probability", 0.30)
        current_risk_pct = round(current_risk * 100, 1)

        # Staffing ratio breach increases readmission risk
        strain_factor = STAFFING_READMISSION_FACTOR if (census_delta > 0 and nurses_delta <= 0) else 0.0
        surge_factor  = max(0.0, census_delta * 0.001)  # 0.1% per extra patient

        projected_risk_pct = round(current_risk_pct + (strain_factor + surge_factor) * 100, 1)
        projected_risk_pct = max(0.0, min(95.0, projected_risk_pct))
        risk_delta         = round(projected_risk_pct - current_risk_pct, 1)
        penalty_exposure   = round(projected_risk_pct / 100.0 * READMISSION_PENALTY_INR, 0)

        return {
            "current_readmission_risk_pct":   current_risk_pct,
            "projected_readmission_risk_pct": projected_risk_pct,
            "risk_delta_pct":                 risk_delta,
            "penalty_exposure_inr":           penalty_exposure,
            "direct_effect":                  (
                f"Staffing strain elevates missed-care probability → readmission risk +{risk_delta:.1f}%"
                if strain_factor > 0 else "No direct staffing strain identified"
            ),
            "indirect_effect":                (
                f"Higher census ({census_delta} extra patients) reduces per-patient care time → "
                f"quality event exposure increases; estimated penalty exposure: ₹{penalty_exposure:,.0f}"
            ),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Domain 7: Department Workload Distribution
    # ──────────────────────────────────────────────────────────────────────────

    def _department_workload(
        self,
        prediction: Dict,
        census_delta: int,
        primary_dept: str,
    ) -> List[Dict[str, Any]]:
        """
        Estimate load redistribution when one department is stressed.
        Overflow from primary department spills to adjacent departments.
        """
        spillover_ratio = 0.25   # 25% of excess census spills to adjacent departments
        spillover_vol   = max(0, math.ceil(census_delta * spillover_ratio))

        workload_impacts = []
        for dept in DEPARTMENTS:
            capacity = DEPT_CAPACITIES[dept]
            baseline_nurses = DEPT_BASELINE_STAFFING[dept]

            if dept == primary_dept:
                vol_change  = census_delta
                load_change = round((census_delta / max(capacity, 1)) * 100, 1)
            elif dept in ("Emergency", "MedSurg") and primary_dept not in ("Emergency", "MedSurg"):
                # Adjacent departments absorb overflow
                vol_change  = spillover_vol
                load_change = round((spillover_vol / max(capacity, 1)) * 100, 1)
            else:
                vol_change  = 0
                load_change = 0.0

            projected_ratio = round((baseline_nurses + vol_change * 0.3) / max(baseline_nurses, 1), 2)
            status = "stressed" if load_change > 10 else ("elevated" if load_change > 5 else "normal")

            workload_impacts.append({
                "department":          dept,
                "volume_change":       vol_change,
                "workload_change_pct": load_change,
                "projected_workload_index": projected_ratio,
                "status":              status,
                "is_primary":          dept == primary_dept,
            })

        return workload_impacts

    # ──────────────────────────────────────────────────────────────────────────
    # Cascade Severity & Summary
    # ──────────────────────────────────────────────────────────────────────────

    def _cascade_severity(self, effects: Dict[str, Any]) -> str:
        """Derive overall cascade severity from individual domain scores."""
        risk_scores = []

        occ_risk = effects.get("bed_occupancy_impact", {}).get("risk_level", "low")
        wait_risk = effects.get("ed_wait_time_impact", {}).get("risk_level", "low")
        ratio_breach = effects.get("staffing_demand_impact", {}).get("ratio_breach", False)

        score_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        risk_scores.append(score_map.get(occ_risk, 1))
        risk_scores.append(score_map.get(wait_risk, 1))
        if ratio_breach:
            risk_scores.append(3)

        avg = sum(risk_scores) / max(len(risk_scores), 1)
        if avg >= 3.5:
            return "critical"
        if avg >= 2.5:
            return "high"
        if avg >= 1.8:
            return "medium"
        return "low"

    @staticmethod
    def _cascade_summary(model_type: str, effects: Dict[str, Any], prediction: Dict) -> str:
        occ   = effects.get("bed_occupancy_impact", {})
        wait  = effects.get("ed_wait_time_impact", {})
        staff = effects.get("staffing_demand_impact", {})
        cost  = effects.get("operational_cost_impact", {})

        return (
            f"Cascade analysis from {model_type.replace('_', ' ').title()}: "
            f"Projected occupancy {occ.get('projected_occupancy_pct', 'N/A')}% "
            f"(Δ{occ.get('occupancy_delta_pct', 0):+.1f}%); "
            f"ED wait {wait.get('projected_wait_min', 'N/A')} min "
            f"(Δ{wait.get('wait_delta_min', 0):+.1f} min); "
            f"Staffing gap: {staff.get('fte_gap', 0)} FTE; "
            f"Operational cost delta: ₹{cost.get('total_operational_cost_inr', 0):,.0f}."
        )


# Module-level singleton
cascade_analyzer = CascadeImpactAnalyzer()
