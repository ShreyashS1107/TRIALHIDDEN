from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.core.security import require_role
from app.models.enums import UserRoleEnum
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import csv

from app.database.session import get_db
from app.services.project import ProjectService
from app.repositories.project import ProjectRepository

router = APIRouter()

def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    repository = ProjectRepository(db)
    return ProjectService(repository)

@router.get(
    "/projects/csv",
    summary="Export Projects CSV",
    description="Streams filtered project list to CSV format for reporting export.",
    response_class=StreamingResponse
)
def export_projects_csv(
    agency: Optional[str] = Query(None, description="Filter by implementing agency"),
    state: Optional[str] = Query(None, description="Filter by location state"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: ProjectService = Depends(get_project_service),
    current_user = Depends(require_role([UserRoleEnum.MOSPI_ADMIN]))
):
    data = service.list_projects(page=1, page_size=10000, agency=agency, state=state, is_active=is_active)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["project_id", "project_name", "agency", "state", "original_cost_crore", "is_active"])
    
    for item in data.items:
        writer.writerow([
            item.project_id,
            item.project_name,
            item.agency,
            item.state,
            item.original_cost_crore,
            item.is_active
        ])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="mospi_projects_export.csv"'}
    )
