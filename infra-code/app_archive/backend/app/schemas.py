from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RunBase(BaseModel):
    id: int
    repo_id: int
    workflow_name: Optional[str]
    head_branch: Optional[str]
    event: Optional[str]
    status: Optional[str]
    conclusion: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_secs: Optional[float]
    url: Optional[str]
    actor: Optional[str]

    class Config:
        from_attributes = True

class JobBase(BaseModel):
    id: int
    run_id: int
    name: Optional[str]
    status: Optional[str]
    conclusion: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_secs: Optional[float]

    class Config:
        from_attributes = True

class StepBase(BaseModel):
    id: int
    job_id: int
    name: Optional[str]
    status: Optional[str]
    conclusion: Optional[str]
    number: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
