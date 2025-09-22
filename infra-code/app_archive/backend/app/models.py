from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Repo(Base):
    __tablename__ = "repos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    full_name = Column(String(512), nullable=False, unique=True)
    default_branch = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    runs = relationship("WorkflowRun", back_populates="repo")

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id = Column(BigInteger, primary_key=True)  # GitHub run_id
    repo_id = Column(Integer, ForeignKey("repos.id"), index=True)
    workflow_name = Column(String(255), nullable=True)
    head_branch = Column(String(255), nullable=True, index=True)
    head_sha = Column(String(64), nullable=True)
    event = Column(String(64), nullable=True)
    status = Column(String(64), nullable=True)       # queued | in_progress | completed
    conclusion = Column(String(64), nullable=True)   # success | failure | cancelled | ...
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_secs = Column(Float, nullable=True)
    url = Column(String(1024), nullable=True)
    actor = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    repo = relationship("Repo", back_populates="runs")
    jobs = relationship("WorkflowJob", back_populates="run")

class WorkflowJob(Base):
    __tablename__ = "workflow_jobs"
    id = Column(BigInteger, primary_key=True)  # GitHub job_id
    run_id = Column(BigInteger, ForeignKey("workflow_runs.id"), index=True)
    name = Column(String(255), nullable=True)
    status = Column(String(64), nullable=True)
    conclusion = Column(String(64), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_secs = Column(Float, nullable=True)

    run = relationship("WorkflowRun", back_populates="jobs")
    steps = relationship("WorkflowStep", back_populates="job")
    log = relationship("RunLog", back_populates="job", uselist=False)

class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, ForeignKey("workflow_jobs.id"), index=True)
    name = Column(String(255), nullable=True)
    status = Column(String(64), nullable=True)
    conclusion = Column(String(64), nullable=True)
    number = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    job = relationship("WorkflowJob", back_populates="steps")

class RunLog(Base):
    __tablename__ = "run_logs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, ForeignKey("workflow_jobs.id"), index=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    storage = Column(String(16), default="disk")
    path = Column(String(1024), nullable=True)
    size_bytes = Column(BigInteger, nullable=True)

    job = relationship("WorkflowJob", back_populates="log")
