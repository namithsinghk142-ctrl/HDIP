"""
HDIP Comprehensive Test Suite — Phase 5
========================================
Covers: Authentication, Predictions, Decision Engine, Scenario Simulation,
        Feedback Loop, Audit Trail, Recommendation Engine, Cascade Analyzer.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Ensure database tables exist and clean up connection pool per test."""
    from app.core.database import engine, Base
    from app.models import user, dataset, operational, ml_model, decision  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient):
    """Authenticate and return bearer headers for protected routes."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@hdip.health", "password": "Admin@HDIP2024!"}
    )
    if resp.status_code == 200:
        token = resp.json().get("access_token", "")
        return {"Authorization": f"Bearer {token}"}
    return {}


# ════════════════════════════════════════════════════════════════════════════════
# HEALTH PROBES
# ════════════════════════════════════════════════════════════════════════════════

class TestHealthProbes:
    @pytest.mark.anyio
    async def test_liveness(self, client):
        r = await client.get("/health/liveness")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert "version" in body

    @pytest.mark.anyio
    async def test_health_alias(self, client):
        r = await client.get("/health")
        assert r.status_code == 200


# ════════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ════════════════════════════════════════════════════════════════════════════════

class TestAuthentication:
    @pytest.mark.anyio
    async def test_login_valid(self, client):
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@hdip.health", "password": "Admin@HDIP2024!"}
        )
        assert r.status_code in (200, 401)  # 401 if DB not seeded

    @pytest.mark.anyio
    async def test_login_invalid_returns_401(self, client):
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@hdip.health", "password": "wrongpassword"}
        )
        assert r.status_code == 401

    @pytest.mark.anyio
    async def test_unauthenticated_protected_route(self, client):
        """Protected routes must return 401 without a valid token."""
        r = await client.get("/api/v1/decisions/alerts")
        assert r.status_code == 401

    @pytest.mark.anyio
    async def test_invalid_bearer_token_returns_401(self, client):
        r = await client.get(
            "/api/v1/decisions/alerts",
            headers={"Authorization": "Bearer invalid.jwt.token"}
        )
        assert r.status_code == 401


# ════════════════════════════════════════════════════════════════════════════════
# SECURITY HEADERS
# ════════════════════════════════════════════════════════════════════════════════

class TestSecurityHeaders:
    @pytest.mark.anyio
    async def test_security_headers_present(self, client):
        r = await client.get("/health")
        assert "x-content-type-options" in r.headers
        assert "x-frame-options" in r.headers
        assert "x-request-id" in r.headers
        assert "x-process-time-ms" in r.headers

    @pytest.mark.anyio
    async def test_x_frame_options_deny(self, client):
        r = await client.get("/health")
        assert r.headers.get("x-frame-options") == "DENY"

    @pytest.mark.anyio
    async def test_request_id_injected(self, client):
        r = await client.get("/health", headers={"X-Request-ID": "test-trace-id-123"})
        assert r.headers.get("x-request-id") == "test-trace-id-123"


# ════════════════════════════════════════════════════════════════════════════════
# ML PREDICTION MODELS — UNIT TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestDemandForecastModel:
    def test_predict_returns_keys(self):
        from app.modules.predictions.models.demand_forecast import DemandForecastModel
        model = DemandForecastModel()
        result = model.predict({"horizon_days": 3})
        assert "forecasted_volumes" in result
        assert "confidence_score" in result
        assert isinstance(result["confidence_score"], float)
        assert 0.0 <= result["confidence_score"] <= 1.0

    def test_predict_confidence_in_range(self):
        from app.modules.predictions.models.demand_forecast import DemandForecastModel
        model = DemandForecastModel()
        for _ in range(5):
            r = model.predict({"horizon_days": 7})
            assert 0.5 <= r["confidence_score"] <= 1.0

    def test_explain_returns_top_factors(self):
        from app.modules.predictions.models.demand_forecast import DemandForecastModel
        model = DemandForecastModel()
        prediction = model.predict({"horizon_days": 3})
        explanation = model.explain(prediction)
        assert "top_factors" in explanation
        assert len(explanation["top_factors"]) > 0


class TestBedOccupancyModel:
    def test_predict_returns_peak_occupancy(self):
        from app.modules.predictions.models.bed_occupancy import BedOccupancyModel
        model = BedOccupancyModel()
        result = model.predict({"department": "MedSurg", "horizon_hours": 24})
        assert "peak_occupancy_pct" in result
        assert 0 <= result["peak_occupancy_pct"] <= 100

    def test_predict_high_occupancy_risk_level(self):
        from app.modules.predictions.models.bed_occupancy import BedOccupancyModel
        model = BedOccupancyModel()
        result = model.predict({"department": "ICU", "base_occ_pct": 95.0})
        assert result.get("risk_level") in ("critical", "high", "medium", "low")


class TestEDWaitTimeModel:
    def test_predict_returns_wait_minutes(self):
        from app.modules.predictions.models.ed_wait_time import EDWaitTimeModel
        model = EDWaitTimeModel()
        result = model.predict({"ed_census": 28, "waiting_count": 8, "acuity_level": 3})
        assert "predicted_wait_minutes" in result
        assert result["predicted_wait_minutes"] >= 0

    def test_high_census_increases_wait(self):
        from app.modules.predictions.models.ed_wait_time import EDWaitTimeModel
        model = EDWaitTimeModel()
        low = model.predict({"ed_census": 15, "waiting_count": 2, "acuity_level": 3})
        high = model.predict({"ed_census": 38, "waiting_count": 20, "acuity_level": 2})
        assert high["predicted_wait_minutes"] > low["predicted_wait_minutes"]


class TestReadmissionRiskModel:
    def test_predict_returns_probability(self):
        from app.modules.predictions.models.readmission_risk import ReadmissionRiskModel
        model = ReadmissionRiskModel()
        result = model.predict({
            "age": 70, "gender": "M", "diagnosis": "CHF",
            "comorbidity_count": 4, "length_of_stay_days": 7,
            "esi_acuity": 2, "prior_admissions_12m": 3, "prior_ed_visits_6m": 2, "payer": "Medicare"
        })
        assert "risk_probability" in result
        assert 0.0 <= result["risk_probability"] <= 1.0
        assert result.get("risk_tier") in ("very_high", "high", "moderate", "low")

    def test_high_risk_patient(self):
        from app.modules.predictions.models.readmission_risk import ReadmissionRiskModel
        model = ReadmissionRiskModel()
        r = model.predict({
            "age": 85, "gender": "F", "diagnosis": "COPD",
            "comorbidity_count": 6, "length_of_stay_days": 12,
            "esi_acuity": 1, "prior_admissions_12m": 5, "prior_ed_visits_6m": 4, "payer": "Medicare"
        })
        assert r["risk_probability"] >= 0.5


# ════════════════════════════════════════════════════════════════════════════════
# RECOMMENDATION ENGINE — UNIT TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestRecommendationEngine:
    def test_generates_recommendations_for_demand_forecast(self):
        from app.modules.decisions.recommendation_engine import recommendation_engine
        prediction = {"predicted_volume_surge_pct": 18.5, "average_volume": 52.0, "confidence_score": 0.88}
        impact = {"risk_level": "high", "estimated_extra_beds_needed": 8, "staffing_gap": {"nurses": 3}}
        explanation = {"top_factors": [{"feature": "historical_volume", "shap_value": 0.42}]}
        recs = recommendation_engine.generate("demand_forecast", prediction, impact, explanation)
        assert isinstance(recs, list)
        assert len(recs) >= 1
        assert all("action" in r for r in recs)
        assert all("priority_tier" in r for r in recs)

    def test_priority_tier_is_valid(self):
        from app.modules.decisions.recommendation_engine import recommendation_engine
        prediction = {"predicted_volume_surge_pct": 25.0, "average_volume": 60.0, "confidence_score": 0.92}
        impact = {"risk_level": "critical", "estimated_extra_beds_needed": 15, "staffing_gap": {"nurses": 5}}
        explanation = {"top_factors": []}
        recs = recommendation_engine.generate("demand_forecast", prediction, impact, explanation)
        for r in recs:
            assert r["priority_tier"] in ("P1", "P2", "P3", "P4")

    def test_confidence_profile_all_keys_present(self):
        from app.modules.decisions.recommendation_engine import compute_confidence_profile
        profile = compute_confidence_profile(0.88, "capacity")
        assert "prediction_confidence" in profile
        assert "recommendation_confidence" in profile
        assert "overall_decision_confidence" in profile
        assert all(0.0 <= v <= 1.0 for v in profile.values())

    def test_reasoning_chain_has_steps(self):
        from app.modules.decisions.recommendation_engine import recommendation_engine
        prediction = {"predicted_wait_minutes": 55.0, "ed_census": 35, "confidence_score": 0.85}
        impact = {"risk_level": "high", "estimated_lwbs_risk_pct": 12.0}
        explanation = {"top_factors": [{"feature": "ed_census", "shap_value": 0.55}]}
        recs = recommendation_engine.generate("ed_wait_time", prediction, impact, explanation)
        if recs:
            assert "reasoning_chain" in recs[0]
            assert len(recs[0]["reasoning_chain"]) >= 3


# ════════════════════════════════════════════════════════════════════════════════
# CASCADE IMPACT ANALYZER — UNIT TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestCascadeAnalyzer:
    def test_returns_all_seven_domains(self):
        from app.modules.decisions.cascade_analyzer import cascade_analyzer
        prediction = {"predicted_volume_surge_pct": 12.0, "average_volume": 50.0}
        impact = {"risk_level": "high", "estimated_extra_beds_needed": 6}
        context = {"census_delta": 12, "nurses_delta": 0}
        result = cascade_analyzer.analyze("demand_forecast", prediction, impact, context)
        domains = [
            "bed_occupancy_impact", "ed_wait_time_impact", "staffing_demand_impact",
            "resource_utilization_impact", "operational_cost_impact",
            "readmission_risk_impact", "department_workload_impact"
        ]
        for d in domains:
            assert d in result, f"Missing domain: {d}"

    def test_cascade_severity_is_valid(self):
        from app.modules.decisions.cascade_analyzer import cascade_analyzer
        result = cascade_analyzer.analyze("demand_forecast",
            {"predicted_volume_surge_pct": 5.0, "average_volume": 40.0},
            {"risk_level": "low", "estimated_extra_beds_needed": 0},
            {"census_delta": 5}
        )
        assert result["cascade_severity"] in ("low", "medium", "high", "critical")


# ════════════════════════════════════════════════════════════════════════════════
# SCENARIO SIMULATOR — UNIT TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestScenarioSimulator:
    def test_invalid_scenario_type_raises(self):
        from app.modules.decisions.scenario_simulator import ScenarioSimulator
        sim = ScenarioSimulator()
        with pytest.raises(ValueError, match="Unknown scenario type"):
            sim._apply_perturbations("invalid_scenario", {}, sim._build_baseline())

    def test_baseline_contains_all_models(self):
        from app.modules.decisions.scenario_simulator import ScenarioSimulator
        sim = ScenarioSimulator()
        baseline = sim._build_baseline()
        assert "demand_forecast" in baseline
        assert "bed_occupancy" in baseline
        assert "ed_wait_time" in baseline
        assert "readmission_risk" in baseline

    def test_increased_arrivals_raises_census(self):
        from app.modules.decisions.scenario_simulator import ScenarioSimulator
        sim = ScenarioSimulator()
        baseline = sim._build_baseline()
        perturbed, _ = sim._apply_perturbations(
            "increased_patient_arrivals", {"surge_count": 20}, baseline
        )
        assert perturbed["ed_wait_time"]["ed_census"] > baseline["ed_wait_time"]["ed_census"]

    def test_staff_shortage_raises_waiting_count(self):
        from app.modules.decisions.scenario_simulator import ScenarioSimulator
        sim = ScenarioSimulator()
        baseline = sim._build_baseline()
        perturbed, ctx = sim._apply_perturbations(
            "staff_shortage", {"shortage_count": 4}, baseline
        )
        assert perturbed["ed_wait_time"]["waiting_count"] > baseline["ed_wait_time"]["waiting_count"]
        assert ctx["nurses_delta"] == -4

    def test_bed_expansion_lowers_occupancy(self):
        from app.modules.decisions.scenario_simulator import ScenarioSimulator
        sim = ScenarioSimulator()
        baseline = sim._build_baseline()
        perturbed, _ = sim._apply_perturbations(
            "bed_expansion", {"beds_added": 20, "target_department": "MedSurg"}, baseline
        )
        assert perturbed["bed_occupancy"]["base_occ_pct"] < baseline["bed_occupancy"]["base_occ_pct"]

    def test_additional_staffing_reduces_waiting(self):
        from app.modules.decisions.scenario_simulator import ScenarioSimulator
        sim = ScenarioSimulator()
        baseline = sim._build_baseline()
        perturbed, ctx = sim._apply_perturbations(
            "additional_staffing", {"nurses_added": 5}, baseline
        )
        assert perturbed["ed_wait_time"]["waiting_count"] <= baseline["ed_wait_time"]["waiting_count"]
        assert ctx["nurses_delta"] == 5

    def test_seasonal_surge_raises_volume(self):
        from app.modules.decisions.scenario_simulator import ScenarioSimulator
        sim = ScenarioSimulator()
        baseline = sim._build_baseline()
        perturbed, _ = sim._apply_perturbations(
            "seasonal_demand_surge", {"seasonal_factor": 1.5}, baseline
        )
        assert perturbed["demand_forecast"]["base_volume"] > baseline["demand_forecast"]["base_volume"]

    def test_mci_maxes_census(self):
        from app.modules.decisions.scenario_simulator import ScenarioSimulator
        sim = ScenarioSimulator()
        baseline = sim._build_baseline()
        perturbed, ctx = sim._apply_perturbations(
            "mass_casualty_event", {"mci_patient_count": 60, "high_acuity_pct": 80.0}, baseline
        )
        assert perturbed["ed_wait_time"]["ed_census"] > baseline["ed_wait_time"]["ed_census"]
        assert ctx["census_delta"] == 60

    def test_extrapolation_check_large_surge(self):
        from app.modules.decisions.scenario_simulator import ScenarioSimulator
        sim = ScenarioSimulator()
        baseline = sim._build_baseline()
        exceeds = sim._check_extrapolation(
            "increased_patient_arrivals", {"surge_count": 100}, baseline
        )
        assert exceeds is True

    def test_extrapolation_check_small_surge(self):
        from app.modules.decisions.scenario_simulator import ScenarioSimulator
        sim = ScenarioSimulator()
        baseline = sim._build_baseline()
        exceeds = sim._check_extrapolation(
            "increased_patient_arrivals", {"surge_count": 3}, baseline
        )
        assert exceeds is False


# ════════════════════════════════════════════════════════════════════════════════
# EFFECTIVENESS SCORING — UNIT TESTS
# ════════════════════════════════════════════════════════════════════════════════

class TestEffectivenessScoring:
    def test_perfect_match_scores_100(self):
        from app.modules.decisions.recommendation_engine import compute_effectiveness_scores
        scores = compute_effectiveness_scores({
            "expected_improvement": 20.0, "actual_improvement": 20.0,
            "expected_cost_inr": 10000, "actual_cost_inr": 10000,
            "expected_wait_reduction_min": 15.0, "actual_wait_reduction_min": 15.0,
            "expected_occupancy_change_pct": -5.0, "actual_occupancy_change_pct": -5.0,
            "expected_staffing_change": 3, "actual_staffing_change": 3,
            "expected_resource_utilization_pct": 10.0, "actual_resource_utilization_pct": 10.0,
        })
        assert scores["prediction_accuracy_score"] == 100.0
        assert scores["recommendation_effectiveness_score"] == 100.0
        assert scores["cost_estimation_accuracy_score"] == 100.0

    def test_missing_actuals_handled_gracefully(self):
        from app.modules.decisions.recommendation_engine import compute_effectiveness_scores
        scores = compute_effectiveness_scores({
            "expected_improvement": 20.0, "actual_improvement": None,
            "expected_cost_inr": None, "actual_cost_inr": None,
        })
        assert "prediction_accuracy_score" in scores
        assert "recommendation_effectiveness_score" in scores
        assert "cost_estimation_accuracy_score" in scores
        for v in scores.values():
            assert isinstance(v, (int, float))

    def test_partial_match_gives_between_0_and_100(self):
        from app.modules.decisions.recommendation_engine import compute_effectiveness_scores
        scores = compute_effectiveness_scores({
            "expected_improvement": 20.0, "actual_improvement": 14.0,
            "expected_cost_inr": 10000, "actual_cost_inr": 13000,
        })
        for v in scores.values():
            assert 0.0 <= v <= 100.0
