from typing import Dict, Any, List, Optional
from datetime import datetime


class ModelMonitor:
    """Enterprise Model Monitoring service for production ML models.
    
    Tracks per-model health metrics:
    - Prediction volume and throughput
    - Average inference latency
    - Confidence/probability distribution
    - Drift status integration
    - Performance metric history
    - Retraining recommendations
    
    Data is stored in-memory for fast access. In production, this would
    persist to a time-series database (e.g., TimescaleDB, InfluxDB).
    """

    def __init__(self):
        self._metrics: Dict[str, Dict[str, Any]] = {}

    def register_model(
        self,
        model_name: str,
        version: str,
        algorithm: str,
        training_metrics: Dict[str, float],
        feature_names: List[str]
    ) -> None:
        """Register a deployed model for monitoring."""
        self._metrics[model_name] = {
            "model_name": model_name,
            "version": version,
            "algorithm": algorithm,
            "status": "active",
            "registered_at": datetime.utcnow().isoformat(),
            "last_trained": datetime.utcnow().isoformat(),
            "training_metrics": training_metrics,
            "feature_names": feature_names,
            "prediction_count": 0,
            "total_latency_ms": 0.0,
            "confidence_histogram": {"high": 0, "medium": 0, "low": 0},
            "drift_status": "healthy",
            "drift_psi": 0.0,
            "needs_retraining": False,
            "performance_history": [],
            "recent_predictions": []
        }

    def record_prediction(
        self,
        model_name: str,
        latency_ms: float,
        confidence: float,
        prediction_value: Any
    ) -> None:
        """Record a prediction event for monitoring."""
        if model_name not in self._metrics:
            return

        m = self._metrics[model_name]
        m["prediction_count"] += 1
        m["total_latency_ms"] += latency_ms

        # Classify confidence
        if confidence >= 0.80:
            m["confidence_histogram"]["high"] += 1
        elif confidence >= 0.60:
            m["confidence_histogram"]["medium"] += 1
        else:
            m["confidence_histogram"]["low"] += 1

        # Keep last 100 predictions for trend analysis
        m["recent_predictions"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": round(confidence, 4),
            "latency_ms": round(latency_ms, 2)
        })
        if len(m["recent_predictions"]) > 100:
            m["recent_predictions"] = m["recent_predictions"][-100:]

    def update_drift_status(
        self,
        model_name: str,
        drift_psi: float,
        drift_status: str,
        needs_retraining: bool
    ) -> None:
        """Update the drift status for a monitored model."""
        if model_name not in self._metrics:
            return

        self._metrics[model_name]["drift_psi"] = drift_psi
        self._metrics[model_name]["drift_status"] = drift_status
        self._metrics[model_name]["needs_retraining"] = needs_retraining

    def record_training_event(
        self,
        model_name: str,
        version: str,
        metrics: Dict[str, float]
    ) -> None:
        """Record a model retraining event."""
        if model_name not in self._metrics:
            return

        self._metrics[model_name]["version"] = version
        self._metrics[model_name]["last_trained"] = datetime.utcnow().isoformat()
        self._metrics[model_name]["training_metrics"] = metrics
        self._metrics[model_name]["performance_history"].append({
            "version": version,
            "trained_at": datetime.utcnow().isoformat(),
            "metrics": metrics
        })

    def get_model_health(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive health report for a single model."""
        if model_name not in self._metrics:
            return None

        m = self._metrics[model_name]
        avg_latency = round(m["total_latency_ms"] / max(m["prediction_count"], 1), 2)

        return {
            "model_name": m["model_name"],
            "version": m["version"],
            "algorithm": m["algorithm"],
            "status": m["status"],
            "registered_at": m["registered_at"],
            "last_trained": m["last_trained"],
            "training_metrics": m["training_metrics"],
            "prediction_count": m["prediction_count"],
            "avg_latency_ms": avg_latency,
            "confidence_distribution": m["confidence_histogram"],
            "drift_status": m["drift_status"],
            "drift_psi": m["drift_psi"],
            "needs_retraining": m["needs_retraining"],
            "retraining_recommendation": self._get_retraining_recommendation(m)
        }

    def get_all_models_health(self) -> List[Dict[str, Any]]:
        """Get health overview for all monitored models."""
        return [self.get_model_health(name) for name in self._metrics]

    def _get_retraining_recommendation(self, m: Dict[str, Any]) -> str:
        """Generate actionable retraining recommendation."""
        if m["needs_retraining"]:
            return "IMMEDIATE - Significant data drift detected. Model accuracy may be degraded."
        if m["drift_status"] == "warning":
            return "SCHEDULED - Minor drift detected. Schedule retraining within 7 days."
        if m["prediction_count"] > 10000:
            return "PERIODIC - High prediction volume. Evaluate model performance."
        return "NONE - Model is healthy and performing within expected parameters."


# Global singleton for application-wide model monitoring
model_monitor = ModelMonitor()
