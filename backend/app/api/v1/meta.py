from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.session import get_db
from app.schemas.portfolio import EpochsResponse

router = APIRouter()

@router.get(
    "/epochs",
    response_model=EpochsResponse,
    summary="Get Reporting Epochs",
    description="Returns the list of all available monthly reporting epochs."
)
def get_epochs(db: Session = Depends(get_db)) -> EpochsResponse:
    sql = text("SELECT DISTINCT report_month FROM monthly_snapshots ORDER BY report_month ASC")
    result = db.execute(sql).fetchall()
    epochs = [row.report_month for row in result if row.report_month]
    return EpochsResponse(total_epochs=len(epochs), available_epochs=epochs)
