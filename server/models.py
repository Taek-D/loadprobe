from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: datetime


class Report(BaseModel):
    id: int
    title: str
    category: str
    location: str
    inspector: str
    description: str
    created_at: str


class ReportsResponse(BaseModel):
    count: int
    reports: list[Report]


class SubmitRequest(BaseModel):
    inspector_name: str = Field(min_length=1, max_length=100)
    location: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=50)
    check_items: list[str] = Field(min_length=1)
    notes: str = ""


class SubmitResponse(BaseModel):
    id: int
    message: str = "Submission recorded"
    submitted_at: str
