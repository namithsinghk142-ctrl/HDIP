import os
import uuid
import pandas as pd
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile, HTTPException, status

from app.models.dataset import Dataset, DatasetColumn, DatasetStatus
from app.modules.data.profiler import DataQualityProfiler
from app.config import settings

class DataService:
    @staticmethod
    async def upload_dataset(
        db: AsyncSession, file: UploadFile, user_id: uuid.UUID, description: Optional[str] = None
    ) -> Dataset:
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV or Excel files are supported."
            )

        dataset_id = uuid.uuid4()
        upload_dir = os.path.join(settings.STORAGE_PATH, "uploads", str(dataset_id))
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Parse dataframe
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to parse dataset file: {str(e)}")

        profile = DataQualityProfiler.profile_dataframe(df)

        # Create dataset entity
        dataset = Dataset(
            id=dataset_id,
            name=file.filename,
            description=description or f"Uploaded dataset {file.filename}",
            file_path=file_path,
            file_size_bytes=len(content),
            row_count=profile["total_rows"],
            column_count=profile["total_columns"],
            status=DatasetStatus.ACTIVE,
            quality_score=profile["quality_score"],
            profile_json=profile,
            uploaded_by_id=user_id
        )

        db.add(dataset)

        # Create columns entity
        for col_info in profile["columns"]:
            col_obj = DatasetColumn(
                dataset_id=dataset_id,
                name=col_info["name"],
                data_type=col_info["data_type"],
                nullable_pct=col_info["nullable_pct"],
                unique_count=col_info["unique_count"],
                min_value=str(col_info.get("min_value")) if col_info.get("min_value") is not None else None,
                max_value=str(col_info.get("max_value")) if col_info.get("max_value") is not None else None,
                mean_value=col_info.get("mean_value"),
                sample_values=col_info.get("sample_values")
            )
            db.add(col_obj)

        await db.commit()
        await db.refresh(dataset)
        return dataset

    @staticmethod
    async def list_datasets(db: AsyncSession) -> List[Dataset]:
        res = await db.execute(select(Dataset).order_by(Dataset.created_at.desc()))
        return res.scalars().all()
