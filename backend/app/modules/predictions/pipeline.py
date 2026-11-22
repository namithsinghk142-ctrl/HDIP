import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.model_selection import StratifiedKFold, cross_val_score
import joblib
import os
import time
import hashlib


class FeatureTransformer:
    """Unified feature engineering and preprocessing pipeline for all HDIP ML models.
    
    Handles:
    - Temporal feature extraction (lags, rolling stats, calendar features)
    - Categorical encoding (one-hot, ordinal, label)
    - Numerical scaling (standard, minmax, robust)
    - Missing value imputation (median, forward-fill)
    - Outlier clipping (IQR-based)
    - Data hash generation for drift baseline tracking
    """

    @staticmethod
    def add_calendar_features(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
        """Extract calendar features from a datetime column."""
        df = df.copy()
        dt = pd.to_datetime(df[date_col])
        df["day_of_week"] = dt.dt.dayofweek
        df["month"] = dt.dt.month
        df["day_of_month"] = dt.dt.day
        df["is_weekend"] = dt.dt.dayofweek.isin([5, 6]).astype(int)
        df["is_winter"] = dt.dt.month.isin([12, 1, 2]).astype(int)
        df["hour"] = dt.dt.hour
        # Cyclical encoding for hour and day_of_week
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)
        df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7.0)
        df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7.0)
        return df

    @staticmethod
    def add_lag_features(series: pd.Series, lags: List[int]) -> pd.DataFrame:
        """Create lag features for a time series."""
        result = pd.DataFrame()
        fill_val = series.mean()
        for lag in lags:
            result[f"lag_{lag}"] = series.shift(lag).fillna(fill_val)
        return result

    @staticmethod
    def add_rolling_features(series: pd.Series, windows: List[int]) -> pd.DataFrame:
        """Create rolling mean and std features."""
        result = pd.DataFrame()
        for w in windows:
            shifted = series.shift(1)  # Avoid look-ahead
            result[f"rolling_{w}_mean"] = shifted.rolling(w, min_periods=1).mean()
            result[f"rolling_{w}_std"] = shifted.rolling(w, min_periods=1).std().fillna(0.0)
        return result

    @staticmethod
    def clip_outliers_iqr(series: pd.Series, factor: float = 1.5) -> pd.Series:
        """Clip outliers using IQR-based bounds."""
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - factor * iqr
        upper = q3 + factor * iqr
        return series.clip(lower, upper)

    @staticmethod
    def impute_median(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """Impute missing values with column median."""
        df = df.copy()
        for col in columns:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].median())
        return df

    @staticmethod
    def compute_data_hash(df: pd.DataFrame) -> str:
        """Generate SHA-256 hash of dataset for drift baseline tracking."""
        raw = pd.util.hash_pandas_object(df).values.tobytes()
        return hashlib.sha256(raw).hexdigest()[:16]


class ModelArtifactManager:
    """Handles serialization, versioning, and loading of ML model artifacts."""

    @staticmethod
    def save_model(model: Any, artifact_dir: str, model_name: str = "model") -> str:
        """Serialize model to disk and return artifact path."""
        os.makedirs(artifact_dir, exist_ok=True)
        path = os.path.join(artifact_dir, f"{model_name}.joblib")
        joblib.dump(model, path)
        return path

    @staticmethod
    def load_model(artifact_dir: str, model_name: str = "model") -> Any:
        """Load serialized model from disk."""
        path = os.path.join(artifact_dir, f"{model_name}.joblib")
        if not os.path.exists(path):
            return None
        return joblib.load(path)

    @staticmethod
    def save_scaler(scaler: Any, artifact_dir: str) -> str:
        """Serialize feature scaler alongside model."""
        os.makedirs(artifact_dir, exist_ok=True)
        path = os.path.join(artifact_dir, "scaler.joblib")
        joblib.dump(scaler, path)
        return path

    @staticmethod
    def save_metadata(metadata: Dict[str, Any], artifact_dir: str) -> str:
        """Save training metadata (feature names, metrics, etc.)."""
        os.makedirs(artifact_dir, exist_ok=True)
        path = os.path.join(artifact_dir, "metadata.joblib")
        joblib.dump(metadata, path)
        return path


class BenchmarkRunner:
    """Benchmarks multiple candidate algorithms and selects the best production model.
    
    Evaluates candidates on:
    - Primary evaluation metric (MAE, RMSE, ROC-AUC, F1)
    - Inference latency (ms)
    - Model complexity / interpretability
    """

    @staticmethod
    def benchmark_regressors(
        candidates: List[Tuple[str, Any]],
        X: np.ndarray,
        y: np.ndarray,
        cv_splits: int = 5,
        scoring: str = "neg_mean_absolute_error"
    ) -> List[Dict[str, Any]]:
        """Benchmark multiple regressors with cross-validation."""
        results = []
        for name, model in candidates:
            start_time = time.time()
            scores = cross_val_score(model, X, y, cv=min(cv_splits, len(X) // 2), scoring=scoring)
            train_time = time.time() - start_time

            # Measure inference latency
            model.fit(X, y)
            latency_start = time.time()
            for _ in range(100):
                model.predict(X[:1])
            avg_latency_ms = ((time.time() - latency_start) / 100) * 1000

            results.append({
                "algorithm": name,
                "cv_score_mean": round(float(-scores.mean()), 4),
                "cv_score_std": round(float(scores.std()), 4),
                "train_time_sec": round(train_time, 3),
                "avg_latency_ms": round(avg_latency_ms, 2),
                "model": model
            })

        results.sort(key=lambda r: r["cv_score_mean"])
        return results

    @staticmethod
    def benchmark_classifiers(
        candidates: List[Tuple[str, Any]],
        X: np.ndarray,
        y: np.ndarray,
        cv_splits: int = 5,
        scoring: str = "roc_auc"
    ) -> List[Dict[str, Any]]:
        """Benchmark multiple classifiers with stratified cross-validation."""
        results = []
        skf = StratifiedKFold(n_splits=min(cv_splits, max(2, int(min(np.bincount(y.astype(int)))))),
                              shuffle=True, random_state=42)

        for name, model in candidates:
            start_time = time.time()
            try:
                scores = cross_val_score(model, X, y, cv=skf, scoring=scoring)
            except Exception:
                scores = np.array([0.5])
            train_time = time.time() - start_time

            model.fit(X, y)
            latency_start = time.time()
            for _ in range(100):
                model.predict(X[:1])
            avg_latency_ms = ((time.time() - latency_start) / 100) * 1000

            results.append({
                "algorithm": name,
                "cv_score_mean": round(float(scores.mean()), 4),
                "cv_score_std": round(float(scores.std()), 4),
                "train_time_sec": round(train_time, 3),
                "avg_latency_ms": round(avg_latency_ms, 2),
                "model": model
            })

        results.sort(key=lambda r: -r["cv_score_mean"])
        return results
