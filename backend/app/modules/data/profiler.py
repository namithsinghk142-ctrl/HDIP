from typing import Dict, Any
import pandas as pd
import numpy as np

class DataProfiler:
    """Automated Data Quality Profiling & Health Assessment Engine for HDIP.
       Evaluates dataset completeness, missingness, duplicate rates, and outlier metrics.
    """

    @staticmethod
    def profile_dataframe(df: pd.DataFrame, dataset_name: str = "Dataset") -> Dict[str, Any]:
        total_rows = len(df)
        if total_rows == 0:
            return {
                "dataset_name": dataset_name,
                "total_rows": 0,
                "total_columns": len(df.columns),
                "health_score": 0.0,
                "status": "empty",
                "column_profiles": [],
                "summary": "Dataset is empty."
            }

        column_profiles = []
        total_missing = 0
        total_cells = total_rows * len(df.columns)

        for col in df.columns:
            col_data = df[col]
            missing_count = int(col_data.isna().sum())
            total_missing += missing_count
            missing_pct = round((missing_count / total_rows) * 100.0, 2)
            unique_count = int(col_data.nunique())
            dtype = str(col_data.dtype)

            profile = {
                "name": col,
                "dtype": dtype,
                "missing_count": missing_count,
                "missing_pct": missing_pct,
                "unique_count": unique_count,
                "sample_values": col_data.dropna().head(3).tolist()
            }

            # Numerical stats if applicable
            if np.issubdtype(col_data.dtype, np.number):
                profile.update({
                    "mean": round(float(col_data.mean()), 2) if not col_data.dropna().empty else None,
                    "std": round(float(col_data.std()), 2) if not col_data.dropna().empty else None,
                    "min": round(float(col_data.min()), 2) if not col_data.dropna().empty else None,
                    "max": round(float(col_data.max()), 2) if not col_data.dropna().empty else None,
                })

            column_profiles.append(profile)

        # Duplicate row count
        duplicate_rows = int(df.duplicated().sum())
        duplicate_pct = round((duplicate_rows / total_rows) * 100.0, 2)

        # Health score calculation (100 - (missing_pct * 0.5 + duplicate_pct * 0.5))
        completeness_pct = 100.0 - (total_missing / total_cells * 100.0 if total_cells > 0 else 0)
        health_score = max(0.0, round(completeness_pct - (duplicate_pct * 0.5), 1))

        status = "excellent" if health_score >= 90.0 else ("good" if health_score >= 75.0 else "warning")

        # Mapped columns format for service consumption
        columns_mapped = [
            {
                "name": col["name"],
                "data_type": col["dtype"],
                "nullable_pct": col["missing_pct"],
                "unique_count": col["unique_count"],
                "min_value": col.get("min"),
                "max_value": col.get("max"),
                "mean_value": col.get("mean"),
                "sample_values": col.get("sample_values"),
            }
            for col in column_profiles
        ]

        return {
            "dataset_name": dataset_name,
            "total_rows": total_rows,
            "total_columns": len(df.columns),
            "completeness_pct": round(completeness_pct, 1),
            "duplicate_count": duplicate_rows,
            "duplicate_pct": duplicate_pct,
            "health_score": health_score,
            "quality_score": health_score,
            "status": status,
            "column_profiles": column_profiles,
            "columns": columns_mapped,
            "summary": f"Dataset contains {total_rows} rows and {len(df.columns)} columns with overall health score of {health_score}%."
        }


# Alias for backward compatibility across data service modules
DataQualityProfiler = DataProfiler

