# Technical Design Document – CI/CD Pipeline Health Dashboard

## 1. Introduction

This document defines the technical design of the CI/CD Pipeline Health Dashboard, a centralized system to monitor, analyze, and visualize the health of CI/CD pipelines across repositories. The dashboard provides real-time visibility into repository runs, jobs, steps, logs, and alerting.

The document covers:

- High-Level Architecture  
- Data Flow  
- Database Schema (ERD)  

---

## 2. High-Level Architecture

The system architecture is divided into four major components:

### Frontend (Dashboard UI)
- Built with **React + Recharts** for data visualization.  
- Displays repository pipelines, run statuses, job breakdowns, logs, and alerts.  
- Supports filtering, drill-downs, and alert acknowledgment.  

### Backend (API + Processing Engine)
- Developed using **Node.js/Express** or **Python/FastAPI**.  
- Provides REST/GraphQL APIs for the frontend.  
- Periodically fetches pipeline run data from external integrations (e.g., GitHub Actions, Jenkins).  
- Processes logs and metrics before persisting to the database.  

### Database (Persistent Storage)
- **PostgreSQL** or **MySQL** as relational DB.  
- Stores repositories, pipeline runs, jobs, steps, logs, and alerts.  
- Supports historical queries for trend analysis.  

### External Integrations
- **CI/CD Providers**: GitHub Actions, GitLab CI, Jenkins.  
- **Notification Channels**: Gmail/SMTP for email alerts, Slack/MS Teams for chat notifications.  

### Architecture Diagram
```
            +------------------+
            |   Frontend (UI)  |
            | React + Recharts |
            +------------------+
                     |
                     v
            +------------------+
            |  Backend (API)   |
            | Node.js/FastAPI  |
            +------------------+
              |   ^        |
              v   |        v
     +----------------+   +----------------+
     | Relational DB  |   | External CI/CD |
     | PostgreSQL     |   | GitHub/Jenkins |
     +----------------+   +----------------+
              |
              v
       +----------------+
       | Notification   |
       | Gmail / Slack  |
       +----------------+
```

---

## 3. Data Flow

The data flow represents how pipeline execution data moves through the system.

### Trigger & Collection
- CI/CD providers (e.g., GitHub Actions) generate run events.  
- Backend ingests these via APIs/webhooks.  

### Processing
- Backend parses events into structured data (repos → runs → jobs → steps).  
- Logs and metrics are processed and normalized.  

### Storage
- Data is stored in the relational DB.  
- Indexed for querying (latest runs, failed jobs, step logs).  

### Visualization
- Frontend queries backend APIs.  
- Displays pipeline health dashboards, historical trends, and alerts.  

### Alerts
- Backend detects failures or anomalies.  
- Sends email (via Gmail SMTP) or chat notifications (Slack).  

### Data Flow Diagram
```
   [CI/CD Provider]
          |
      (Events/Webhooks)
          |
          v
   [Backend API Layer] -- (Alert Rules) --> [Notification Services]
          |
          v
   [Database Storage]
          |
          v
   [Frontend Dashboard]
```

---

## 4. Database Schema (ERD)

The Entity Relationship Diagram (ERD) models how pipeline entities relate to each other.

### Key Entities
- **Repositories**: Source code repos connected to the dashboard.  
- **Runs**: Each pipeline execution.  
- **Jobs**: A run consists of multiple jobs (build, test, deploy).  
- **Steps**: A job consists of multiple steps.  
- **Logs**: Captures step/job execution logs.  
- **Alerts**: Tracks triggered alerts on failures.  

### ERD
```
+----------------+        +---------------+
|  Repositories  |1------∞|     Runs      |
| repo_id (PK)   |        | run_id (PK)   |
| name           |        | repo_id (FK)  |
| owner          |        | status        |
+----------------+        | start_time    |
                          | end_time      |
                          +---------------+
                                  |
                                  |1
                                  ∞
                          +---------------+
                          |     Jobs      |
                          | job_id (PK)   |
                          | run_id (FK)   |
                          | name          |
                          | status        |
                          | start_time    |
                          | end_time      |
                          +---------------+
                                  |
                                  |1
                                  ∞
                          +---------------+
                          |    Steps      |
                          | step_id (PK)  |
                          | job_id (FK)   |
                          | name          |
                          | status        |
                          | logs_id (FK)  |
                          +---------------+
                                  |
                                  |1
                                  ∞
                          +---------------+
                          |     Logs      |
                          | log_id (PK)   |
                          | step_id (FK)  |
                          | log_text      |
                          | timestamp     |
                          +---------------+
                                  |
                                  |1
                                  ∞
                          +---------------+
                          |    Alerts     |
                          | alert_id (PK) |
                          | run_id (FK)   |
                          | severity      |
                          | message       |
                          | created_at    |
                          | resolved_at   |
                          +---------------+
```
