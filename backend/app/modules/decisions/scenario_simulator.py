"""
Scenario Simulator — Phase 4 Decision Intelligence
===================================================
Runs 8 operational scenario types by perturbing ML model input parameters
and re-executing the full prediction → impact → cascade → recommendation pipeline.

Each simulation produces a structured SimulationResult with:
  - baseline_state:   current predictions across all relevant models
  - simulated_state:  predictions under scenario conditions
  - delta:            metric-by-metric comparison (baseline vs simulated)
  - cascade_effects:  7-domain downstream impacts from CascadeImpactAnalyzer
  - recommendations:  scenario-specific data-driven recommendations
  - confidence_profile: simulation confidence (includes scenario_simulation_confidence)

Supported Scenarios:
  1. increased_patient_arrivals   — surge_count added to census
  2. staff_shortage               — nurses removed, wait time increases
  3. additional_staffing          — nurses added, wait time decreases
  4. bed_expansion                — beds added, occupancy decreases
  5. department_closure           — routes volume to other departments
  6. equipment_downtime           — treatment time increases, boarding rises
  7. seasonal_demand_surge        — multiplies base volume by seasonal_factor
  8. mass_casualty_event          — maximises census/acuity, disables elective
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from app.modules.decisions.cascade_analyzer import cascade_analyzer
from app.modules.decisions.recommendation_engine import (
    recommendation_engine,
    compute_confidence_profile,
)


# ──────────────────────────────────────────────────────────────────────────────
# Scenario Definitions
# ──────────────────────────────────────────────────────────────────────────────

SCENARIO_CATALOG = {
    "increased_patient_arrivals": {
        "label":       "Increased Patient Arrivals",
        "description": "Simulate a surge in patient arrivals above baseline census.",
        "parameters":  [
            {"name": "surge_count",       "label": "Additional Patients",     "type": "int",   "default": 15,  "min": 1,   "max": 80},
            {"name": "surge_duration_h",  "label": "Duration (hours)",        "type": "int",   "default": 6,   "min": 1,   "max": 24},
        ],
    },
    "staff_shortage": {
        "label":       "Staff Shortage",
        "description": "Model the operational impact of an unexpected nurse shortage.",
        "parameters":  [
            {"name": "shortage_count",    "label": "Nurses Unavailable",      "type": "int",   "default": 3,   "min": 1,   "max": 20},
            {"name": "shortage_shift",    "label": "Affected Shift",          "type": "str",   "default": "Day"},
        ],
    },
    "additional_staffing": {
        "label":       "Additional Staffing",
        "description": "Estimate the benefit of deploying additional nursing staff.",
        "parameters":  [
            {"name": "nurses_added",      "label": "Additional Nurses",       "type": "int",   "default": 4,   "min": 1,   "max": 20},
            {"name": "target_department", "label": "Target Department",       "type": "str",   "default": "Emergency"},
        ],
    },
    "bed_expansion": {
        "label":       "Bed Expansion",
        "description": "Model the impact of opening additional beds in a department.",
        "parameters":  [
            {"name": "beds_added",        "label": "Beds to Open",            "type": "int",   "default": 8,   "min": 1,   "max": 50},
            {"name": "target_department", "label": "Target Department",       "type": "str",   "default": "MedSurg"},
        ],
    },
    "department_closure": {
        "label":       "Department Closure",
        "description": "Estimate load redistribution when a department is closed or restricted.",
        "parameters":  [
            {"name": "closed_department", "label": "Department to Close",     "type": "str",   "default": "Oncology"},
            {"name": "closure_pct",       "label": "Capacity Reduction (%)",  "type": "float", "default": 100.0, "min": 10.0, "max": 100.0},
        ],
    },
    "equipment_downtime": {
        "label":       "Equipment Downtime",
        "description": "Simulate operational impact when critical equipment is out of service.",
        "parameters":  [
            {"name": "downtime_hours",    "label": "Equipment Downtime (h)",  "type": "int",   "default": 4,   "min": 1,   "max": 72},
            {"name": "treatment_time_increase_min", "label": "Added Treatment Time (min)", "type": "int", "default": 15, "min": 5, "max": 60},
        ],
    },
    "seasonal_demand_surge": {
        "label":       "Seasonal Demand Surge",
        "description": "Model the impact of seasonal illness peaks (flu, RSV, winter surge).",
        "parameters":  [
            {"name": "seasonal_factor",   "label": "Demand Multiplier (×)",   "type": "float", "default": 1.25, "min": 1.05, "max": 2.0},
            {"name": "season_name",       "label": "Season / Event",          "type": "str",   "default": "Winter Flu Peak"},
        ],
    },
    "mass_casualty_event": {
        "label":       "Mass Casualty Event (MCI)",
        "description": "Simulate emergency preparedness under a mass-casualty incident.",
        "parameters":  [
            {"name": "mci_patient_count", "label": "MCI Patients",            "type": "int",   "default": 40,  "min": 10,  "max": 200},
            {"name": "high_acuity_pct",   "label": "High-Acuity Patient %",   "type": "float", "default": 70.0, "min": 20.0, "max": 100.0},
        ],
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Scenario Simulator
# ──────────────────────────────────────────────────────────────────────────────

class ScenarioSimulator:
    """
    Orchestrates scenario simulation across all four HDIP prediction models.

    For each scenario:
    1. Build baseline model inputs from current default parameters
    2. Apply scenario-specific perturbations
    3. Run all affected models with perturbed inputs (lazy import to avoid cycles)
    4. Run CascadeImpactAnalyzer on results
    5. Generate scenario-specific recommendations
    6. Compute simulation confidence profile
    """

    def simulate(
        self,
        scenario_type: str,
        scenario_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Main simulation entry point.

        Returns:
            SimulationResult dict with all comparison data, cascade effects,
            recommendations, and confidence profile.

        Raises:
            ValueError: if scenario_type is not in SCENARIO_CATALOG
        """
        if scenario_type not in SCENARIO_CATALOG:
            raise ValueError(
                f"Unknown scenario type '{scenario_type}'. "
                f"Supported: {list(SCENARIO_CATALOG.keys())}"
            )

        catalog_entry = SCENARIO_CATALOG[scenario_type]

        # Step 1: Build baseline
        baseline = self._build_baseline()

        # Step 2 + 3: Apply perturbations and get perturbed predictions
        perturbed_inputs, delta_context = self._apply_perturbations(
            scenario_type, scenario_params, baseline
        )
        simulated = self._run_perturbed_models(perturbed_inputs)

        # Step 4: Cascade analysis
        primary_model = list(simulated.keys())[0]
        primary_pred  = simulated[primary_model].get("prediction", {})
        primary_impact = simulated[primary_model].get("impact", {})
        cascade        = cascade_analyzer.analyze(
            primary_model, primary_pred, primary_impact, delta_context
        )

        # Step 5: Generate recommendations from simulated state
        primary_explanation = simulated[primary_model].get("explanation", {"top_factors": []})
        recommendations = recommendation_engine.generate(
            primary_model, primary_pred, primary_impact, primary_explanation
        )

        # Step 6: Confidence profile with scenario-level penalties
        n_params     = len([v for v in scenario_params.values() if v is not None])
        exceeds_30pct = self._check_extrapolation(scenario_type, scenario_params, baseline)
        base_conf    = primary_pred.get("confidence_score", 0.87)
        conf_profile = compute_confidence_profile(
            prediction_confidence=base_conf,
            category="capacity",
            scenario_applicable=True,
            perturbed_param_count=n_params,
            any_param_exceeds_30pct=exceeds_30pct,
        )

        # Build delta comparison
        delta = self._compute_delta(baseline, simulated, cascade)

        return {
            "scenario_type":       scenario_type,
            "scenario_label":      catalog_entry["label"],
            "scenario_params":     scenario_params,
            "simulated_at":        datetime.utcnow().isoformat(),
            "confidence_profile":  conf_profile,
            "baseline_state":      baseline,
            "simulated_state":     simulated,
            "delta":               delta,
            "cascade_effects":     cascade,
            "recommendations":     recommendations,
            "cascade_severity":    cascade.get("cascade_severity", "medium"),
            "cascade_summary":     cascade.get("cascade_summary", ""),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Baseline Builder
    # ──────────────────────────────────────────────────────────────────────────

    def _build_baseline(self) -> Dict[str, Any]:
        """Build baseline model inputs representing current hospital state."""
        from app.modules.decisions.engine import decision_engine  # lazy import

        class _FakeDB:
            """Minimal async DB stub for baseline prediction (no DB needed for inputs)."""
            pass

        # Build baseline inputs for each model
        return {
            "demand_forecast": {
                "horizon_days": 3,
                "base_volume":  45,
            },
            "bed_occupancy": {
                "department":    "MedSurg",
                "horizon_hours": 24,
                "base_occ_pct":  82.0,
            },
            "ed_wait_time": {
                "ed_census":      28,
                "waiting_count":  8,
                "acuity_level":   3,
                "hour":           datetime.now().hour,
            },
            "readmission_risk": {
                "age":                  65,
                "gender":               "M",
                "diagnosis":            "Pneumonia",
                "comorbidity_count":    3,
                "length_of_stay_days":  5,
                "esi_acuity":           3,
                "prior_admissions_12m": 1,
                "prior_ed_visits_6m":   2,
                "payer":                "Medicare",
            },
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Perturbation Logic (8 Scenarios)
    # ──────────────────────────────────────────────────────────────────────────

    def _apply_perturbations(
        self,
        scenario_type: str,
        params: Dict[str, Any],
        baseline: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Apply scenario-specific parameter perturbations to baseline inputs.

        Returns:
            (perturbed_inputs, delta_context)
            delta_context is passed to CascadeImpactAnalyzer as extra context.
        """
        if scenario_type not in SCENARIO_CATALOG:
            raise ValueError(
                f"Unknown scenario type '{scenario_type}'. "
                f"Supported: {list(SCENARIO_CATALOG.keys())}"
            )

        inputs = {k: dict(v) for k, v in baseline.items()}   # deep copy
        delta_context: Dict[str, Any] = {
            "census_delta":  0,
            "nurses_delta":  0,
            "beds_delta":    0,
            "scenario_type": scenario_type,
        }

        if scenario_type == "increased_patient_arrivals":
            surge      = int(params.get("surge_count", 15))
            inputs["ed_wait_time"]["ed_census"]     += surge
            inputs["ed_wait_time"]["waiting_count"] += math.ceil(surge * 0.6)
            inputs["demand_forecast"]["base_volume"] = baseline["demand_forecast"]["base_volume"] + surge
            delta_context["census_delta"] = surge

        elif scenario_type == "staff_shortage":
            shortage = int(params.get("shortage_count", 3))
            # Shortage increases effective waiting count (fewer nurses → longer queue)
            inputs["ed_wait_time"]["waiting_count"] += math.ceil(shortage * 2.5)
            inputs["ed_wait_time"]["ed_census"]     += math.ceil(shortage * 1.5)
            delta_context["nurses_delta"] = -shortage
            delta_context["census_delta"] = math.ceil(shortage * 1.5)

        elif scenario_type == "additional_staffing":
            added = int(params.get("nurses_added", 4))
            # More nurses reduce effective waiting count
            inputs["ed_wait_time"]["waiting_count"] = max(0, inputs["ed_wait_time"]["waiting_count"] - math.ceil(added * 2.0))
            delta_context["nurses_delta"] = added

        elif scenario_type == "bed_expansion":
            beds    = int(params.get("beds_added", 8))
            dept    = params.get("target_department", "MedSurg")
            inputs["bed_occupancy"]["department"] = dept
            # Occupancy decreases as effective capacity increases
            current_occ = inputs["bed_occupancy"]["base_occ_pct"]
            capacity_map = {"Emergency": 40, "ICU": 25, "MedSurg": 120, "Pediatrics": 30, "Cardiology": 45, "Oncology": 35}
            cap          = capacity_map.get(dept, 100)
            new_occ      = round(current_occ * cap / (cap + beds), 1)
            inputs["bed_occupancy"]["base_occ_pct"] = max(30.0, new_occ)
            delta_context["beds_delta"] = beds

        elif scenario_type == "department_closure":
            closure_pct = float(params.get("closure_pct", 100.0))
            # Rerouted volume lands on ED and MedSurg
            rerouted = math.ceil(15 * (closure_pct / 100.0))
            inputs["ed_wait_time"]["ed_census"]     += rerouted
            inputs["ed_wait_time"]["waiting_count"] += math.ceil(rerouted * 0.5)
            inputs["bed_occupancy"]["base_occ_pct"] = min(98.0, inputs["bed_occupancy"]["base_occ_pct"] + rerouted * 0.5)
            delta_context["census_delta"] = rerouted

        elif scenario_type == "equipment_downtime":
            downtime_h = int(params.get("downtime_hours", 4))
            treat_inc  = int(params.get("treatment_time_increase_min", 15))
            # Increased treatment time → more boarding → higher wait
            boarding_increase = math.ceil(downtime_h * 1.5)
            inputs["ed_wait_time"]["waiting_count"] += boarding_increase
            inputs["ed_wait_time"]["ed_census"]     += math.ceil(boarding_increase * 0.8)
            delta_context["census_delta"] = math.ceil(boarding_increase * 0.8)

        elif scenario_type == "seasonal_demand_surge":
            factor = float(params.get("seasonal_factor", 1.25))
            base_vol  = baseline["demand_forecast"]["base_volume"]
            surged_vol = round(base_vol * factor)
            surge_delta = surged_vol - base_vol
            inputs["demand_forecast"]["base_volume"]  = surged_vol
            inputs["ed_wait_time"]["ed_census"]        = min(40, inputs["ed_wait_time"]["ed_census"] + math.ceil(surge_delta * 0.6))
            inputs["ed_wait_time"]["waiting_count"]   += math.ceil(surge_delta * 0.4)
            inputs["bed_occupancy"]["base_occ_pct"]   = min(97.0, inputs["bed_occupancy"]["base_occ_pct"] + surge_delta * 0.4)
            delta_context["census_delta"] = math.ceil(surge_delta * 0.6)

        elif scenario_type == "mass_casualty_event":
            mci_count       = int(params.get("mci_patient_count", 40))
            high_acuity_pct = float(params.get("high_acuity_pct", 70.0))
            inputs["ed_wait_time"]["ed_census"]      = min(40, 28 + mci_count)
            inputs["ed_wait_time"]["waiting_count"]  = mci_count
            inputs["ed_wait_time"]["acuity_level"]   = 2   # all ESI 1/2
            inputs["bed_occupancy"]["base_occ_pct"]  = min(99.0, 85 + mci_count * 0.35)
            inputs["demand_forecast"]["base_volume"] = baseline["demand_forecast"]["base_volume"] + mci_count
            delta_context["census_delta"] = mci_count
            delta_context["nurses_delta"] = -5   # nurses pulled from other departments

        return inputs, delta_context

    # ──────────────────────────────────────────────────────────────────────────
    # Run Perturbed Models
    # ──────────────────────────────────────────────────────────────────────────

    def _run_perturbed_models(
        self, perturbed_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run all four prediction models with perturbed inputs.
        Uses lazy import to avoid circular dependency with engine.py.
        """
        from app.modules.decisions.engine import decision_engine  # lazy import

        results: Dict[str, Any] = {}
        for model_type, params in perturbed_inputs.items():
            try:
                model = decision_engine.models.get(model_type)
                if model is None:
                    continue
                prediction  = model.predict(params)
                explanation = model.explain(prediction)
                impact      = decision_engine._assess_impact(model_type, prediction)
                results[model_type] = {
                    "prediction":  prediction,
                    "explanation": explanation,
                    "impact":      impact,
                }
            except Exception as exc:
                results[model_type] = {"error": str(exc)}

        return results

    # ──────────────────────────────────────────────────────────────────────────
    # Delta Computation
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_delta(
        self,
        baseline: Dict[str, Any],
        simulated: Dict[str, Any],
        cascade: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute baseline vs simulated metric deltas."""
        occ_impact  = cascade.get("bed_occupancy_impact", {})
        wait_impact = cascade.get("ed_wait_time_impact", {})
        staff_impact = cascade.get("staffing_demand_impact", {})
        cost_impact  = cascade.get("operational_cost_impact", {})

        return {
            "bed_occupancy_delta_pct":      occ_impact.get("occupancy_delta_pct", 0),
            "ed_wait_time_delta_min":        wait_impact.get("wait_delta_min", 0),
            "staffing_fte_gap_delta":        staff_impact.get("fte_gap", 0),
            "operational_cost_delta_inr":    cost_impact.get("total_operational_cost_inr", 0),
            "readmission_risk_delta_pct":    cascade.get("readmission_risk_impact", {}).get("risk_delta_pct", 0),
            "resource_utilization_delta_pct": cascade.get("resource_utilization_impact", {}).get("utilization_change_pct", 0),
            "cascade_severity":              cascade.get("cascade_severity", "medium"),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Extrapolation Check
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _check_extrapolation(
        scenario_type: str,
        params: Dict[str, Any],
        baseline: Dict[str, Any],
    ) -> bool:
        """
        Returns True if any parameter exceeds ±30% of the training baseline,
        which increases the extrapolation penalty in confidence scoring.
        """
        base_vol = baseline["demand_forecast"]["base_volume"]  # ≈ 45
        base_census = baseline["ed_wait_time"]["ed_census"]    # ≈ 28

        if scenario_type == "increased_patient_arrivals":
            return int(params.get("surge_count", 15)) > base_census * 0.3
        if scenario_type == "seasonal_demand_surge":
            return float(params.get("seasonal_factor", 1.25)) > 1.30
        if scenario_type == "mass_casualty_event":
            return int(params.get("mci_patient_count", 40)) > base_census * 1.0
        return False


# Scenario catalog for API access
def get_scenario_catalog() -> List[Dict[str, Any]]:
    return [
        {
            "scenario_type": stype,
            **{k: v for k, v in entry.items()},
        }
        for stype, entry in SCENARIO_CATALOG.items()
    ]


# Module-level singleton
scenario_simulator = ScenarioSimulator()
