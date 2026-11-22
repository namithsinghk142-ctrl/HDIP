from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.modules.data.service import DataService

router = APIRouter(prefix="/data", tags=["Data Management"])

@router.get("/datasets")
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    datasets = await DataService.list_datasets(db)
    return [
        {
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "file_size_bytes": d.file_size_bytes,
            "row_count": d.row_count,
            "column_count": d.column_count,
            "status": d.status.value,
            "quality_score": d.quality_score,
            "created_at": d.created_at
        }
        for d in datasets
    ]

@router.post("/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = await DataService.upload_dataset(db, file, current_user.id, description)
    return {
        "id": dataset.id,
        "name": dataset.name,
        "status": dataset.status.value,
        "quality_score": dataset.quality_score,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count
    }
