import os
import sys
import asyncio
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.core.database import AsyncSessionLocal, Base, engine
from app.models.ml_model import MLModel
from app.modules.predictions.models.demand_forecast import DemandForecastModel
from app.modules.predictions.models.bed_occupancy import BedOccupancyModel
from app.modules.predictions.models.ed_wait_time import EDWaitTimeModel
from app.modules.predictions.models.readmission_risk import ReadmissionRiskModel
from app.modules.predictions.monitoring import model_monitor
from sqlalchemy import select

async def init_models():
    print("Training and Registering Phase 3 Enterprise Production Models...")

    # Ensure all DB tables exist
    # Import all models to register them with Base.metadata
    from app.models import user, dataset, operational, ml_model, decision  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Database tables created/verified")

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "synthetic")
    enc_path = os.path.join(data_dir, "patient_encounters.csv")
    bed_path = os.path.join(data_dir, "bed_census.csv")

    if not os.path.exists(enc_path):
        print("Synthetic dataset missing. Run 'python scripts/seed_data.py' first.")
        return

    enc_df = pd.read_csv(enc_path)
    bed_df = pd.read_csv(bed_path)

    # 1. Train Demand Forecast Model
    demand_model = DemandForecastModel()
    res_demand = demand_model.train(enc_df)
    print(f"[OK] Trained Demand Forecast Model (MAE: {res_demand['metrics']['mae']})")
    model_monitor.register_model("demand_forecast", "v1.0.0", "LightGBM_Regressor", res_demand['metrics'], list(res_demand['feature_importance'].keys()))

    # 2. Train Bed Occupancy Model
    occ_model = BedOccupancyModel()
    res_occ = occ_model.train(bed_df)
    print(f"[OK] Trained Bed Occupancy Model (MAE Beds: {res_occ['metrics']['mae_beds']})")
    model_monitor.register_model("bed_occupancy", "v1.0.0", "HistGradientBoosting_Regressor", res_occ['metrics'], list(res_occ['feature_importance'].keys()))

    # 3. Train ED Wait Time Model
    ed_model = EDWaitTimeModel()
    res_ed = ed_model.train(enc_df)
    print(f"[OK] Trained ED Wait Time Model (MAE Min: {res_ed['metrics']['mae_minutes']})")
    model_monitor.register_model("ed_wait_time", "v1.0.0", "XGBoost_Regressor", res_ed['metrics'], list(res_ed['feature_importance'].keys()))

    # 4. Train 30-Day Readmission Risk Model
    readm_model = ReadmissionRiskModel()
    res_readm = readm_model.train(enc_df)
    print(f"[OK] Trained Readmission Risk Model (ROC-AUC: {res_readm['metrics']['roc_auc']})")
    model_monitor.register_model("readmission_risk", "v1.0.0", "XGBoost_Classifier", res_readm['metrics'], list(res_readm['feature_importance'].keys()))

    # Save metadata to DB Enterprise Model Registry
    async with AsyncSessionLocal() as session:
        models_to_register = [
            ("demand_forecast", "LightGBM_Regressor", res_demand, demand_model.artifact_dir),
            ("bed_occupancy", "HistGradientBoosting_Regressor", res_occ, occ_model.artifact_dir),
            ("ed_wait_time", "XGBoost_Regressor", res_ed, ed_model.artifact_dir),
            ("readmission_risk", "XGBoost_Classifier", res_readm, readm_model.artifact_dir)
        ]

        for m_type, algo, res, art_dir in models_to_register:
            r = await session.execute(select(MLModel).where(MLModel.model_type == m_type))
            existing = r.scalar_one_or_none()
            if not existing:
                m = MLModel(
                    model_type=m_type,
                    version=1,
                    algorithm=algo,
                    metrics_json=res["metrics"],
                    feature_names=list(res["feature_importance"].keys()),
                    artifact_path=art_dir,
                    is_active=True
                )
                session.add(m)
            else:
                existing.metrics_json = res["metrics"]
                existing.algorithm = algo

        await session.commit()
        print("[OK] Registered All Phase 3 Models in Enterprise Database Registry & Model Monitor")

if __name__ == "__main__":
    asyncio.run(init_models())
