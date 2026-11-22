import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Integer, Float, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Scenario(Base):
    """Saved scenario simulation results with confidence scoring."""
    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    scenario_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    perturbations_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    baseline_state_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    simulated_state_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    cascade_result_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    recommendations_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    simulation_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, archived
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class OperationalAlert(Base):
    """Proactive operational alerts with lifecycle status tracking."""
    __tablename__ = "operational_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # low, medium, high, critical
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    context_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    recommendations_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, resolved, expired
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class RecommendationTemplate(Base):
    """Configurable recommendation templates seeded per model type."""
    __tablename__ = "recommendation_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    trigger_condition_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    action_template: Mapped[str] = mapped_column(String(500), nullable=False)
    impact_formula: Mapped[str] = mapped_column(String(500), nullable=False)
    urgency_rule: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # capacity, staffing, financial, process
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DecisionAuditLog(Base):
    """
    Full audit trail of every recommendation that was acted upon.

    Lifecycle: pending → implemented → outcome_recorded
    Stores the complete multi-level confidence profile and reasoning chain at
    the moment the decision was made for retrospective accuracy analysis.
    """
    __tablename__ = "decision_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    priority_tier: Mapped[str] = mapped_column(String(10), nullable=False)   # P1, P2, P3, P4
    priority_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    action_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # exact action with numbers

    # Multi-level confidence profile stored at decision time
    confidence_profile_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Full expected outcome metrics for comparison with actuals
    expected_outcome_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Complete reasoning chain: prediction → SHAP → impact → decision → outcome
    reasoning_chain_json: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # Decision action taken
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # accepted, rejected, deferred
    action_note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    acted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    acted_by_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Lifecycle
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    # pending → implemented → outcome_recorded

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    implemented_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class DecisionOutcome(Base):
    """
    Decision Effectiveness tracking — compares predicted vs actual results
    across 6 operational dimensions after a recommendation is implemented.

    Effectiveness scores (0–100) are computed on write and stored for
    fast aggregation in the Recommendation Quality dashboard panel.
    """
    __tablename__ = "decision_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("decision_audit_log.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Dimension 1: General operational improvement
    expected_improvement: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_improvement: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Dimension 2: Cost (INR)
    expected_cost_inr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_cost_inr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Dimension 3: Wait time reduction (minutes)
    expected_wait_reduction_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_wait_reduction_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Dimension 4: Bed occupancy change (percentage points)
    expected_occupancy_change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_occupancy_change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Dimension 5: Staffing change (FTE count)
    expected_staffing_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_staffing_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Dimension 6: Resource utilization change (percentage)
    expected_resource_utilization_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_resource_utilization_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Computed effectiveness scores (0–100), stored on write
    prediction_accuracy_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recommendation_effectiveness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost_estimation_accuracy_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Context
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    recorded_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    recorded_by_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

