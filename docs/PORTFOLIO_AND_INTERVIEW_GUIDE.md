# HDIP — Portfolio & Interview Guide

## Resume-Ready Project Description

### One-Line Summary
> Built a production-grade, AI-powered Hospital Decision Intelligence Platform in Python/FastAPI/React with 4 ML prediction models, SHAP explainability, 8-type scenario simulation, cascading impact analysis, and a complete decision governance audit trail — deployed on Docker with CI/CD.

### Bullet Points for Resume

```
Hospital Decision Intelligence Platform (HDIP) | Python · FastAPI · React · PostgreSQL · Docker
─────────────────────────────────────────────────────────────────────────────────────────────────
• Architected and implemented a full-stack enterprise healthcare AI platform across 5 phases, 
  transforming raw hospital data into explainable, actionable operational intelligence.

• Built 4 production ML models (Prophet demand forecasting, XGBoost bed occupancy, 
  Gradient Boosting ED wait time, XGBoost+LR readmission risk) serving real-time predictions 
  via async FastAPI endpoints.

• Implemented SHAP-based Explainable AI (XAI) with plain-English clinical attribution 
  narratives, enabling hospital administrators to understand and trust ML predictions.

• Designed a quantitative Decision Intelligence Engine with formula-driven recommendations 
  ranked P1–P4, multi-level confidence profiling (Prediction, Recommendation, Scenario, Overall), 
  and 5-step reasoning chain transparency.

• Engineered an 8-scenario operational simulator (patient surges, staff shortages, MCI events) 
  that perturbs ML model inputs and estimates downstream effects across 7 operational domains 
  (staffing, beds, wait times, cost, readmission risk, etc.).

• Built a complete MLOps framework: versioned Enterprise Model Registry, real-time performance 
  monitoring, statistical data drift detection with Celery background jobs, and automated alerts.

• Implemented a Decision Outcome Feedback Loop comparing 6-dimension predicted vs. actual 
  outcomes to compute rolling recommendation quality metrics (effectiveness, accuracy scores).

• Designed a governance-grade Decision Audit Trail tracking every accepted/rejected/deferred 
  decision with actor, reasoning chain, confidence profile, and full lifecycle status.

• Hardened the platform for production: multi-stage Docker builds, non-root container execution, 
  JWT + RBAC (5 roles), security headers (HSTS/CSP/X-Frame-Options), structured JSON logging, 
  request tracing (X-Request-ID), and GitHub Actions CI/CD pipeline.

• Delivered 8 analytics dashboards (Staffing, Financial, ED Flow, Quality & Safety, 
  Executive Decision Center, Scenario Simulator, Decision History, ML Monitoring) using 
  React 18 + Ant Design + Apache ECharts.
```

---

## Recruiter-Friendly Feature Summary

| Category | Feature | Technology |
|---|---|---|
| **Full-Stack Architecture** | React + FastAPI + PostgreSQL + Redis + Nginx | Python, TypeScript |
| **Machine Learning** | 4 production prediction models | scikit-learn, XGBoost, Prophet |
| **Explainable AI** | SHAP attribution with plain-English narratives | SHAP library |
| **Decision Intelligence** | Formula-driven recommendations + confidence profiling | Custom engine |
| **Scenario Simulation** | 8 what-if scenario types with cascade analysis | Custom simulator |
| **MLOps** | Enterprise Model Registry + drift detection + monitoring | Celery, Redis |
| **Security** | JWT auth + RBAC + security headers + request tracing | FastAPI middleware |
| **DevOps** | Docker multi-stage + Docker Compose + GitHub Actions CI/CD | Docker, GitHub Actions |
| **Testing** | 40+ pytest tests across all ML and DI components | pytest-asyncio |
| **Analytics** | 4 specialty analytics dashboards with ECharts | React, ECharts |

---

## Technical Interview Talking Points

### 1. "Why did you use FastAPI over Django or Flask?"
> FastAPI's native async/await support was essential — we have multiple concurrent ML inference calls, database queries, and background tasks. FastAPI's Pydantic v2 integration provides automatic request/response validation with zero boilerplate, and the automatic OpenAPI documentation generation was critical for the team's API-first design approach. Flask would require significant async retrofitting; Django REST framework carries unnecessary ORM overhead for an ML inference service.

### 2. "How does your SHAP implementation work?"
> Each ML model implements an `.explain(prediction)` method that computes SHAP values for the prediction's input features. We use TreeExplainer for tree-based models (XGBoost) for computational efficiency. The raw SHAP float values are then mapped through a feature-to-clinical-narrative dictionary that converts technical feature names and their signed magnitudes into plain-English clinical statements that hospital administrators can understand. This bridges the interpretability gap between ML outputs and operational decision-making.

### 3. "Why Weighted Harmonic Mean for overall decision confidence?"
> We needed a single confidence number that honestly reflects the weakest link in the decision pipeline. Arithmetic mean would mask a weak scenario confidence behind a strong prediction confidence. The Weighted Harmonic Mean (WHM) mathematically penalizes outlier-low values disproportionately — a recommendation with 95% prediction confidence but 40% scenario confidence yields ~57% overall via WHM vs. 67% via arithmetic mean. In healthcare, understating confidence is far safer than overstating it.

### 4. "How does your Scenario Simulator handle multiple models?"
> The ScenarioSimulator builds a baseline input parameter set representing current hospital state across all 4 models. Each scenario type then applies mathematically-derived perturbations (e.g., staff shortage → waiting_count += ceil(shortage × 2.5), census += ceil(shortage × 1.5)). These perturbed inputs are passed through all affected ML models, producing new predictions. Those predictions then flow into the CascadeImpactAnalyzer for 7-domain downstream effect estimation, and finally into the RecommendationEngine for mitigation actions. The full pipeline runs synchronously within a single API call.

### 5. "How do you handle data drift in production?"
> The model_monitor module maintains a rolling window of recent predictions per model. Drift detection computes statistical divergence between recent input feature distributions and the training-time baseline using simplified distribution comparison (expandable to KS-test or PSI for production). When drift score exceeds configurable thresholds, the system automatically creates an OperationalAlert with severity escalation (low/medium/high/critical) and flags the model in the Registry. Celery background jobs run drift detection on a scheduled basis via Redis-backed task queue.

### 6. "Describe the Decision Audit Trail design."
> Every interaction with a recommendation creates a `DecisionAuditLog` record capturing: the full recommendation text and action detail, priority score/tier, multi-level confidence profile (serialized JSON), the 5-step reasoning chain, expected outcome projections, the action taken (accepted/rejected/deferred), actor identity, and timestamps. The record transitions through states: pending → implemented → outcome_recorded. The `DecisionOutcome` table then captures actual results across 6 dimensions, enabling computation of 3 effectiveness scores. This creates an auditable, time-stamped history of every operational decision made using the system — analogous to a clinical decision support audit trail.

### 7. "What security measures did you implement?"
> Five layers: (1) JWT Bearer authentication with bcrypt password hashing, (2) Role-Based Access Control with a 5-role hierarchy and `require_roles()` FastAPI dependency, (3) Security Headers middleware applying HSTS, CSP, X-Frame-Options DENY, X-Content-Type-Options, and XSS Protection to every response, (4) Request Tracing middleware injecting unique X-Request-IDs for distributed tracing, and (5) multi-stage Docker builds running as a non-root user with minimal runtime dependencies.

### 8. "How does the cascading impact analyzer work?"
> CascadeImpactAnalyzer takes a model_type, the prediction output, impact assessment, and a delta_context (census_delta, nurses_delta, beds_delta) and applies domain-specific formulas to estimate downstream effects. For example, a census_delta of +15 patients translates to approximately +12.5 minutes additional wait time (census × 0.75 factor), +2.5 FTE nursing gap (census / 6), and +₹35,000 additional operational cost (staffing × overtime formula). Each domain returns direct and indirect effect descriptions plus quantitative deltas — creating a 7-domain cascade map that transforms a single operational change into a full hospital system impact picture.

---

## Project Stats

| Metric | Count |
|---|---|
| Total source files | ~85 |
| Backend Python modules | ~40 |
| Frontend React components/pages | ~35 |
| REST API endpoints | ~55 |
| ML prediction models | 4 |
| Analytics dashboards | 8 |
| Database tables | 9 |
| Decision scenario types | 8 |
| Cascade analysis domains | 7 |
| Test cases | 40+ |
| Docker containers | 5 |
| Documentation files | 6 |
| Lines of production code | ~8,500 |
