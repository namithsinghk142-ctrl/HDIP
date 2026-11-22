import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime


class DriftDetector:
    """Lightweight enterprise Data Drift Detection engine using Population Stability Index (PSI).
    
    Monitors:
    - Feature distribution shifts (PSI per feature)
    - Missing value rate changes
    - Unexpected categorical values
    - Numerical distribution shifts (mean/std delta)
    
    Drift Severity Thresholds:
    - PSI < 0.10  → Healthy (no action)
    - 0.10 <= PSI < 0.25 → Warning (monitor closely)
    - PSI >= 0.25 → Action Required (flag for retraining)
    """

    PSI_HEALTHY = 0.10
    PSI_WARNING = 0.25

    @staticmethod
    def compute_psi(baseline: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
        """Calculate Population Stability Index between baseline and current distributions.
        
        PSI = sum( (current_pct - baseline_pct) * ln(current_pct / baseline_pct) )
        """
        # Remove NaN values
        baseline = baseline[~np.isnan(baseline)]
        current = current[~np.isnan(current)]

        if len(baseline) < 10 or len(current) < 10:
            return 0.0

        # Create bins from baseline distribution
        breakpoints = np.percentile(baseline, np.linspace(0, 100, bins + 1))
        breakpoints = np.unique(breakpoints)
        if len(breakpoints) < 3:
            return 0.0

        # Compute histograms
        baseline_counts, _ = np.histogram(baseline, bins=breakpoints)
        current_counts, _ = np.histogram(current, bins=breakpoints)

        # Convert to percentages with smoothing to avoid division by zero
        epsilon = 1e-6
        baseline_pct = (baseline_counts / len(baseline)) + epsilon
        current_pct = (current_counts / len(current)) + epsilon

        # Normalize
        baseline_pct = baseline_pct / baseline_pct.sum()
        current_pct = current_pct / current_pct.sum()

        psi = float(np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct)))
        return round(max(0.0, psi), 4)

    @staticmethod
    def compute_missing_rate(series: pd.Series) -> float:
        """Calculate the missing value rate for a feature."""
        if len(series) == 0:
            return 0.0
        return round(float(series.isna().sum() / len(series)), 4)

    @staticmethod
    def detect_feature_drift(
        baseline_df: pd.DataFrame,
        current_df: pd.DataFrame,
        numerical_cols: List[str],
        categorical_cols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run full drift analysis across numerical and categorical features.
        
        Returns per-feature PSI scores, missing rates, and overall drift status.
        """
        feature_reports = []
        overall_psi_scores = []
        alerts = []

        # Numerical feature drift
        for col in numerical_cols:
            if col not in baseline_df.columns or col not in current_df.columns:
                continue

            baseline_vals = baseline_df[col].dropna().values.astype(float)
            current_vals = current_df[col].dropna().values.astype(float)

            psi = DriftDetector.compute_psi(baseline_vals, current_vals)
            overall_psi_scores.append(psi)

            baseline_missing = DriftDetector.compute_missing_rate(baseline_df[col])
            current_missing = DriftDetector.compute_missing_rate(current_df[col])
            missing_delta = round(current_missing - baseline_missing, 4)

            baseline_mean = round(float(np.mean(baseline_vals)), 4) if len(baseline_vals) > 0 else 0.0
            current_mean = round(float(np.mean(current_vals)), 4) if len(current_vals) > 0 else 0.0
            mean_shift = round(current_mean - baseline_mean, 4)

            status = "healthy"
            if psi >= DriftDetector.PSI_WARNING:
                status = "action_required"
                alerts.append(f"Feature '{col}' shows significant drift (PSI={psi})")
            elif psi >= DriftDetector.PSI_HEALTHY:
                status = "warning"

            feature_reports.append({
                "feature": col,
                "type": "numerical",
                "psi_score": psi,
                "status": status,
                "baseline_missing_rate": baseline_missing,
                "current_missing_rate": current_missing,
                "missing_rate_delta": missing_delta,
                "baseline_mean": baseline_mean,
                "current_mean": current_mean,
                "mean_shift": mean_shift
            })

        # Categorical feature drift (check for unexpected values)
        if categorical_cols:
            for col in categorical_cols:
                if col not in baseline_df.columns or col not in current_df.columns:
                    continue

                baseline_cats = set(baseline_df[col].dropna().unique())
                current_cats = set(current_df[col].dropna().unique())
                unexpected = current_cats - baseline_cats

                status = "healthy"
                if unexpected:
                    status = "warning"
                    alerts.append(f"Feature '{col}' has unexpected categories: {unexpected}")

                feature_reports.append({
                    "feature": col,
                    "type": "categorical",
                    "psi_score": 0.0,
                    "status": status,
                    "baseline_categories": len(baseline_cats),
                    "current_categories": len(current_cats),
                    "unexpected_values": list(unexpected)[:5]
                })

        # Overall drift summary
        avg_psi = round(float(np.mean(overall_psi_scores)), 4) if overall_psi_scores else 0.0
        overall_status = "healthy"
        if avg_psi >= DriftDetector.PSI_WARNING:
            overall_status = "action_required"
        elif avg_psi >= DriftDetector.PSI_HEALTHY:
            overall_status = "warning"

        needs_retraining = overall_status == "action_required"

        return {
            "overall_psi": avg_psi,
            "overall_status": overall_status,
            "needs_retraining": needs_retraining,
            "features": feature_reports,
            "alerts": alerts,
            "analyzed_at": datetime.utcnow().isoformat()
        }
