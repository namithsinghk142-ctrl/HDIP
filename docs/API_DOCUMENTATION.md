# HDIP — REST API Documentation

## Base URL
All endpoints are prefixed with `/api/v1`.

**Interactive Docs:** `http://localhost/api/v1/docs` (Swagger UI)
**ReDoc:** `http://localhost/api/v1/redoc`

## Authentication
All protected routes require a Bearer JWT token:
```
Authorization: Bearer <access_token>
```

---

## Authentication Endpoints

### POST /auth/login
Authenticates a user and returns a JWT access token.

**Request:**
```json
{ "username": "admin@hdip.health", "password": "Admin@HDIP2024!" }
```
**Response:**
```json
{ "access_token": "eyJ...", "token_type": "bearer", "user": { "id": "...", "email": "...", "role": "admin" } }
```

### GET /auth/me
Returns the authenticated user's profile.

---

## Analytics Endpoints

### GET /analytics/staffing/summary
Returns staffing analytics including nurse-to-patient ratios, shift coverage, and overtime metrics.

### GET /analytics/financial/summary
Returns financial analytics including revenue, cost breakdown, and margin analysis.

### GET /analytics/ed-flow/summary
Returns ED flow analytics including door-to-doctor time, LWBS rate, and boarding statistics.

### GET /analytics/quality/summary
Returns quality and safety metrics including HCAHPS scores, infection rates, and incident tracking.

---

## Predictions Endpoints

### POST /predictions/demand-forecast
**Body:** `{ "horizon_days": 7 }`
**Response:** Forecasted patient volumes by day with confidence intervals and SHAP attribution.

### POST /predictions/bed-occupancy
**Body:** `{ "department": "MedSurg", "horizon_hours": 24, "base_occ_pct": 82.0 }`
**Response:** Peak occupancy %, capacity buffer, risk level, SHAP attribution.

### POST /predictions/ed-wait-time
**Body:** `{ "ed_census": 28, "waiting_count": 8, "acuity_level": 3, "hour": 14 }`
**Response:** Predicted wait minutes, LWBS risk %, risk level, SHAP attribution.

### POST /predictions/readmission-risk
**Body:** `{ "age": 70, "gender": "M", "diagnosis": "CHF", "comorbidity_count": 4, ... }`
**Response:** Risk probability (0–1), risk_tier, SHAP attribution.

### GET /predictions/registry
Returns the Enterprise ML Model Registry with all registered model versions.

### GET /predictions/monitoring
Returns real-time ML model performance metrics, drift scores, and alert counts.

---

## Decision Intelligence Endpoints

### GET /decisions/alerts
Returns active proactive operational alerts.
**Query params:** `severity` (critical/high/medium/low), `is_acknowledged` (bool)

### POST /decisions/alerts/{id}/acknowledge
Acknowledges an operational alert.

### POST /decisions/evaluate
Runs the full Decision Engine pipeline for a specified model.
**Body:** `{ "model_type": "demand_forecast", "input_params": { "horizon_days": 3 } }`
**Response:** Full decision package including prediction, explanation, impact, recommendations, and multi-level confidence profile.

### GET /decisions/scenarios/catalog
Returns all 8 supported scenario types with parameter definitions.

### POST /decisions/simulate
Runs a scenario simulation.
**Body:**
```json
{
  "scenario_type": "staff_shortage",
  "scenario_params": { "shortage_count": 4, "shortage_shift": "Day" },
  "name": "Weekend Staff Shortage Analysis"
}
```
**Query params:** `save_to_db=true` to persist the result.
**Response:** Full SimulationResult with baseline, simulated states, delta, cascade effects, recommendations, and confidence profile.

### GET /decisions/scenarios
Lists all saved scenario simulations.

### GET /decisions/scenarios/{id}
Returns full detail of a saved scenario.

### GET /decisions/recommendations
Returns current ranked recommendations across all 4 production ML models.

### POST /decisions/recommendations/accept
Accepts a recommendation and logs it to the Decision Audit Trail.
**Body:** `{ "model_type": "demand_forecast", "recommendation": {...}, "note": "Approved by CFO" }`

### POST /decisions/recommendations/reject
Rejects or defers a recommendation.
**Body:** `{ "model_type": "...", "recommendation": {...}, "action": "rejected"|"deferred", "note": "..." }`

### GET /decisions/audit-log
Returns the full Decision Audit Trail.
**Query params:** `action`, `model_type`, `status`

### POST /decisions/audit-log/{id}/mark-implemented
Transitions an accepted decision to "implemented" status.

### POST /decisions/audit-log/{id}/outcome
Submits actual operational outcomes for an implemented decision (Feedback Loop).
**Body:**
```json
{
  "actual_improvement": 22.5,
  "actual_cost_inr": 18000,
  "actual_wait_reduction_min": 14.0,
  "actual_occupancy_change_pct": -4.5,
  "actual_staffing_change": 3,
  "actual_resource_utilization_pct": 11.2,
  "notes": "Exceeded projected wait time reduction by 2 minutes."
}
```
**Response:** 3 computed effectiveness scores.

### GET /decisions/effectiveness
Returns aggregated recommendation effectiveness metrics by model type.

### GET /decisions/executive-summary
Returns the complete Executive Decision Center data package (KPIs, alerts, recommendations, effectiveness).

---

## Data Endpoints

### GET /data/datasets
Lists all uploaded datasets with profiling status.

### POST /data/datasets
Uploads a new dataset (multipart/form-data).

### GET /data/datasets/{id}/health
Returns data quality health report for a dataset.

### GET /data/datasets/{id}/profile
Returns the statistical profiling result for a dataset.

---

## Health Endpoints

### GET /health
### GET /health/liveness
Returns service liveness status.

### GET /health/readiness
Returns database connectivity and service readiness status.

---

## Standard Response Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (invalid input) |
| 401 | Unauthorized (missing or invalid token) |
| 403 | Forbidden (insufficient role privileges) |
| 404 | Not Found |
| 422 | Validation Error (Pydantic schema mismatch) |
| 500 | Internal Server Error |
| 503 | Service Unavailable (database disconnect) |

## Response Headers

| Header | Description |
|---|---|
| `X-Request-ID` | Unique request trace identifier |
| `X-Process-Time-MS` | Server-side processing time in milliseconds |
| `X-Frame-Options` | DENY |
| `X-Content-Type-Options` | nosniff |
| `Strict-Transport-Security` | max-age=31536000; includeSubDomains |
