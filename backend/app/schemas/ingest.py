from pydantic import Field
from app.schemas.common import BaseSchema

class IngestionResponse(BaseSchema):
    task_id: str = Field(..., description="Background worker task UUID")
    status: str = Field(..., description="Task status (e.g. QUEUED)")
    report_month: str = Field(..., description="Target reporting month")
    message: str = Field(..., description="Status message")
