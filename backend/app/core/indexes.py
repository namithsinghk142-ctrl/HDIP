"""
Database Index Definitions — Phase 5 Performance Optimization
=============================================================
Adds targeted composite indexes on high-traffic query paths
identified by query analysis of HDIP's core modules.

Covered patterns:
  - Audit log queries filtered by action + model_type + status
  - Alert queries filtered by is_acknowledged + severity
  - Scenario queries ordered by created_at
  - ML model queries filtered by model_type + is_active
  - Dataset queries filtered by status
"""

from sqlalchemy import Index
from app.models.decision import DecisionAuditLog, OperationalAlert, Scenario, DecisionOutcome
from app.models.ml_model import MLModel


# ── Decision Audit Log Indexes ─────────────────────────────────────────────────
idx_audit_log_action_model = Index(
    "ix_audit_log_action_model_type",
    DecisionAuditLog.action,
    DecisionAuditLog.model_type,
)
idx_audit_log_status = Index(
    "ix_audit_log_status",
    DecisionAuditLog.status,
)
idx_audit_log_created_at = Index(
    "ix_audit_log_created_at",
    DecisionAuditLog.created_at.desc(),
)

# ── Operational Alert Indexes ──────────────────────────────────────────────────
idx_alert_acknowledged_severity = Index(
    "ix_alert_acknowledged_severity",
    OperationalAlert.is_acknowledged,
    OperationalAlert.severity,
)
idx_alert_created_at = Index(
    "ix_alert_created_at",
    OperationalAlert.created_at.desc(),
)

# ── Scenario Indexes ───────────────────────────────────────────────────────────
idx_scenario_type_created = Index(
    "ix_scenario_type_created_at",
    Scenario.scenario_type,
    Scenario.created_at.desc(),
)

# ── ML Model Indexes ───────────────────────────────────────────────────────────
idx_ml_model_type_active = Index(
    "ix_ml_model_type_active",
    MLModel.model_type,
    MLModel.is_active,
)
idx_ml_model_registered_at = Index(
    "ix_ml_model_created_at",
    MLModel.created_at.desc(),
)

# ── Decision Outcome Indexes ───────────────────────────────────────────────────
idx_outcome_audit_id = Index(
    "ix_outcome_audit_log_id",
    DecisionOutcome.audit_log_id,
)
