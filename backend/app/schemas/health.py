from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    service: str = Field(..., examples=["GlampBook API"])
    version: str = Field(..., examples=["1.0.0"])
    environment: str = Field(..., examples=["development"])
    timestamp: datetime = Field(..., description="UTC timestamp of the response")

    model_config = {"json_schema_extra": {"example": {
        "status": "ok",
        "service": "GlampBook API",
        "version": "1.0.0",
        "environment": "development",
        "timestamp": "2024-01-01T00:00:00Z",
    }}}
