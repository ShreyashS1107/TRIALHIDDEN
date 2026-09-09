# SIH26103 Backend

## 1. Overview

The **SIH26103 Backend** is the core API and data-orchestration service for the AI-powered infrastructure project monitoring platform (Ministry of Statistics and Programme Implementation — MoSPI / PAIMANA monitoring problem statement).

Its role in the overall SIH26103 platform:
- Serve as the unified, high-performance API backend powering the frontend web dashboard.
- Connect securely to the central **Supabase PostgreSQL** database housing longitudinal project time-series, historical benchmarks, and surveillance scores.
- Act as the integration bridge for the predictive machine learning models and deterministic execution surveillance metrics developed in `ai-ml/`.
- Provide role-based access control (RBAC) and operational intelligence for project managers, nodal officers, and MoSPI administrators.

---

## 2. Current Status

| Phase | Description | Status |
|---|---|---|
| **Phase 1** | FastAPI Foundation & Health Endpoint | ✅ COMPLETE |
| **Phase 2A** | Database Schema & Relationship Audit | ✅ COMPLETE |
| **Phase 2B** | Supabase PostgreSQL Connection & Pool | ✅ COMPLETE |
| **Phase 3A** | ORM Architecture & Nullability Design | ✅ COMPLETE |
| **Phase 3B** | SQLAlchemy 2.x ORM Model Implementation | ✅ COMPLETE |
| **Phase 4A** | Pydantic v2 API Schema Layer | ✅ COMPLETE |
| **Phase 4B — Part 1** | Read-Only Project Business APIs | ✅ COMPLETE |
| **Phase 4B — Part 2** | Risk Ranking, Surveillance & Alert APIs | ✅ COMPLETE |
| **Phase 5A** | ML Pipeline & Repository Integration Audit | ✅ COMPLETE |
| **Phase 5B-1** | Modular Offline Batch Scoring Engine | ✅ COMPLETE |
| **Phase 5B-2** | Database Ingestion & Pipeline Orchestration | ✅ COMPLETE |
| **Phase 5C-1** | Modular Execution Surveillance Engine (Pillar 2 ESI) | ✅ COMPLETE |
| **Phase 5C-2** | Execution Surveillance Database Ingestion Pipeline | ✅ COMPLETE |
| **Phase 5D** | FastAPI Integration of Stored ML + ESI Intelligence | ✅ COMPLETE |

> [!NOTE]
> **Phase 5D is complete**: Clean, frontend-ready FastAPI integration of precomputed ML risk scores and Execution Stress Index (ESI) surveillance intelligence from Supabase PostgreSQL.
> Exposes `GET /api/v1/projects/{project_id}/intelligence` (unified single-project dossier with null-safe component handling) and `GET /api/v1/analytics/summary` (dynamic portfolio-level metrics, distributions, and report epochs).
> Safe, environment-configurable CORS policy registered.
> Validated with 72/72 backend tests (61 baseline + 11 new) and 89/89 AI-ML regression tests passing.
> Live Supabase database verified before and after smoke testing with zero mutations across all tables.
> **ML INFERENCE INSIDE FASTAPI: NOT IMPLEMENTED**.
> **ESI COMPUTATION INSIDE FASTAPI: NOT IMPLEMENTED**.
> **FASTAPI READS PRECOMPUTED INTELLIGENCE FROM POSTGRESQL**.

---

## 3. Architecture

```text
       Frontend (React / Web Dashboard)
                      ↓ (HTTP / REST)
       FastAPI API Layer (/api/v1)
                      ↓
       Pydantic v2 Schema Layer (Request / Response Validation)
                      ↓
       Service Layer (Business Logic & Error Handling)
                      ↓
       Repository Layer (SQLAlchemy Queries, Filters, Pagination)
                      ↓
       SQLAlchemy 2.x ORM Layer (Mapped Models)
                      ↓ (psycopg2-binary + SSL)
       Supabase PostgreSQL Database (Source of Truth)
                      ↑
    [Batch ML Pipeline Integration Point (ai-ml/)]
        (AUDITED IN PHASE 5A — NOT INTEGRATED YET)
```

- **Database Layer**: Central PostgreSQL database hosted on Supabase containing raw longitudinal snapshots, derived Layer B metrics, Layer C ML risk predictions, and Pillar 2 Execution Stress Index (ESI) scores.
- **ORM Layer**: Modern SQLAlchemy 2.x Declarative Models representing all master, transactional, surveillance, and archive tables.
- **Repository Layer** (`app/repositories/`): Pure database query encapsulation handling deterministic ordering, limit/offset pagination, and filter conditions.
- **Service Layer** (`app/services/`): Business orchestration, 404 entity resolution, and schema transformations.
- **API Routes** (`app/api/v1/`): FastAPI endpoints managing path/query parameters, dependency injection, and HTTP status codes.
- **ML Integration Point**: Direct linkage between offline batch predictions (`ai-ml/`) and backend models (`ml_risk_scores`, `execution_stress_scores`), marked as **NOT IMPLEMENTED YET**.

---

## 4. Folder Structure

The exact current file tree of the `backend/` directory:

```text
backend/
├── .env                       # Local private environment variables (DO NOT COMMIT)
├── .env.example               # Template environment configuration
├── .gitignore                 # Git ignore rules protecting .env and caches
├── README.md                  # Developer handoff documentation
├── requirements.txt           # Production and test dependencies
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI application entrypoint and root routing
│   ├── api/
│   │   ├── __init__.py        # API root router
│   │   └── v1/
│   │       ├── __init__.py    # Version 1 API router aggregator
│   │       ├── alerts.py      # Operational alerts API endpoints
│   │       ├── analytics.py   # Risk rankings and ESI surveillance API endpoints
│   │       ├── health.py      # Non-blocking health check endpoint
│   │       └── projects.py    # Read-only project business API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Settings management via pydantic-settings
│   │   └── exceptions.py      # Base custom application exceptions
│   ├── database/
│   │   ├── __init__.py        # Database package exports (Base, engine, get_db, SessionLocal)
│   │   ├── base.py            # SQLAlchemy 2.x DeclarativeBase definition
│   │   └── session.py         # Engine pool, URL normalization, and get_db dependency
│   ├── models/
│   │   ├── __init__.py        # Clean exports of all ORM models and Enums
│   │   ├── alert.py           # SystemAlert model
│   │   ├── anomaly.py         # DataAnomalyLog model
│   │   ├── archive.py         # CompletedProject and NewlyAddedProject models
│   │   ├── dossier.py         # ProjectMonthlyDossier read-only view model
│   │   ├── enums.py           # Python Enum definitions for PostgreSQL enum types
│   │   ├── execution.py       # ExecutionStressScore (Pillar 2) model
│   │   ├── project.py         # Project master and MonthlySnapshot models
│   │   ├── risk.py            # MLRiskScore (Layer C) model
│   │   └── user.py            # User authentication and RBAC model
│   ├── repositories/
│   │   ├── __init__.py        # Repository exports
│   │   ├── alert.py           # AlertRepository data access layer
│   │   ├── project.py         # ProjectRepository data access layer
│   │   ├── risk.py            # RiskRepository data access layer
│   │   └── surveillance.py    # SurveillanceRepository data access layer
│   ├── schemas/
│   │   ├── __init__.py        # Clean exports of all Pydantic response schemas
│   │   ├── alert.py           # SystemAlertResponse and PaginatedAlertsResponse
│   │   ├── common.py          # BaseSchema with ConfigDict(from_attributes=True)
│   │   ├── dossier.py         # ProjectMonthlyDossierResponse analytical view schema
│   │   ├── execution.py       # ExecutionStressScoreResponse and PaginatedSurveillanceResponse
│   │   ├── project.py         # ProjectSummary, ProjectDetail, PaginatedProjectsResponse
│   │   ├── risk.py            # MLRiskScoreResponse and PaginatedRiskRankingsResponse
│   │   └── snapshot.py        # MonthlySnapshotResponse and SeriesResponse schemas
│   └── services/
│       ├── __init__.py        # Service exports
│       ├── alert.py           # AlertService business orchestration layer
│       ├── analytics.py       # AnalyticsService business orchestration layer
│       └── project.py         # ProjectService business orchestration layer
└── tests/
    ├── __init__.py
    ├── test_alert_api.py      # System alerts API tests
    ├── test_analytics_api.py  # Risk rankings and surveillance API tests
    ├── test_database.py       # Live connection and SELECT 1 tests
    ├── test_health.py         # API health check and degradation tests
    ├── test_models.py         # ORM reflection, constraint, and read-only tests
    ├── test_project_api.py    # Project business API integration tests
    └── test_schemas.py        # Pydantic v2 serialization and validation tests
```

---

## 5. Database

- **Source of Truth**: The remote **Supabase PostgreSQL** instance is the single source of truth. The backend does NOT redesign tables or change database schemas.
- **ORM**: **SQLAlchemy 2.x** using `Mapped[...]` and `mapped_column(...)`.
- **Database Driver**: `psycopg2-binary` using the `postgresql+psycopg2://` dialect with mandatory SSL (`sslmode=require`).
- **Connection Configuration**: Configured in `app/database/session.py` with `pool_pre_ping=True`, `pool_size=10`, `max_overflow=20`, `pool_recycle=300`, and `pool_timeout=30`.
- **Schema & Migrations**: Defined in `database/schema.sql` and `database/migrations/` (`001`, `002`, `003`). The backend does NOT modify these files.
- **Safety**: The backend does **NOT** run `Base.metadata.create_all()` anywhere. No schema modifications or migrations are run automatically.

---

## 6. ORM Models

| Model Class | Table / View | Purpose |
|---|---|---|
| `Project` | `projects` | Canonical master records for ongoing infrastructure projects. |
| `MonthlySnapshot` | `monthly_snapshots` | Layer A raw longitudinal monthly facts (21,555 records). |
| `MLRiskScore` | `ml_risk_scores` | Layer C multi-dimensional risk scores (15,769 records). |
| `ExecutionStressScore` | `execution_stress_scores` | Pillar 2 operational surveillance scores across 5 dimensions + ESI. |
| `SystemAlert` | `system_alerts` | Operational system alerts and ML anomaly notices. |
| `DataAnomalyLog` | `data_anomalies_log` | Ingestion and data quality audit log (1,868 anomalies). |
| `CompletedProject` | `completed_projects` | Historical archive of completed projects. |
| `NewlyAddedProject` | `newly_added_projects` | Staging log of intake projects newly inducted during Flash Reports. |
| `User` | `users` | User accounts and role-based permissions (`MOSPI_ADMIN`, `NODAL_OFFICER`, `PUBLIC_VIEWER`). |
| `ProjectMonthlyDossier` | `v_project_monthly_dossier` | Read-only model reflecting the 60-column derived analytics SQL view. |

---

## 7. Pydantic v2 API Schemas

Implemented under `app/schemas/` with `ConfigDict(from_attributes=True)`:

| Schema Class | Module | Description | Key Fields |
|---|---|---|---|
| `ProjectSummary` | `project.py` | High-level portfolio summary | `project_id`, `project_name`, `agency`, `state`, `original_cost_crore`, `is_active` |
| `ProjectDetail` | `project.py` | Full project detail with milestones | Inherits summary + `legacy_ocms_code`, `approval_start_date`, `original_completion_date`, timestamps |
| `PaginatedProjectsResponse` | `project.py` | Paginated project listing wrapper | `items: List[ProjectSummary]`, `page`, `page_size`, `total` |
| `MonthlySnapshotResponse` | `snapshot.py` | Single monthly snapshot observation | `snapshot_id`, `report_month`, revised cost, cumulative expenditure, physical progress |
| `MonthlySnapshotSeriesResponse` | `snapshot.py` | Chronological collection of snapshots | `project_id`, `total_snapshots`, `snapshots: List[...]` |
| `MLRiskScoreResponse` | `risk.py` | ML risk predictions & component weights | `schedule_delay_risk`, `cost_overrun_risk`, `selected_integrated_risk`, `risk_band`, `dominant_component` |
| `PaginatedRiskRankingsResponse` | `risk.py` | Paginated risk rankings wrapper | `items: List[MLRiskScoreResponse]`, `page`, `page_size`, `total` |
| `ExecutionStressScoreResponse` | `execution.py` | ESI operational surveillance indicators | 5 stress dimensions (`s_*`), 5 flags (`flag_*`), `execution_stress_index`, `esi_tier`, `dominant_stressor`, `suggested_action` |
| `PaginatedSurveillanceResponse` | `execution.py` | Paginated surveillance scores wrapper | `items: List[ExecutionStressScoreResponse]`, `page`, `page_size`, `total` |
| `SystemAlertResponse` | `alert.py` | Operational alerts & warnings | `alert_id`, `alert_code`, `severity`, `alert_source`, `message`, `status`, acknowledgement details |
| `PaginatedAlertsResponse` | `alert.py` | Paginated alerts wrapper | `items: List[SystemAlertResponse]`, `page`, `page_size`, `total` |
| `ProjectMonthlyDossierResponse` | `dossier.py` | 60-column analytical dossier response | Unified payload combining Layer A facts, Layer B derived metrics, Layer C ML signals, and Pillar 2 ESI scores |

---

## 8. API Endpoints

### Foundation Endpoints
| Method | Endpoint | Description | Status |
|---|---|---|---|
| `GET` | `/api/v1/health` | Service and database connectivity health check | Working |
| `GET` | `/docs` | Interactive Swagger API documentation | Working |
| `GET` | `/openapi.json` | OpenAPI v3 specification JSON | Working |

### Project Business APIs (Phase 4B — Part 1)
| Method | Endpoint | Description | Response Schema |
|---|---|---|---|
| `GET` | `/api/v1/projects` | Paginated list of projects with agency, state, is_active filters | `PaginatedProjectsResponse` |
| `GET` | `/api/v1/projects/{project_id}` | Detailed project attributes and milestones (404 if not found) | `ProjectDetail` |
| `GET` | `/api/v1/projects/{project_id}/snapshots` | Chronological monthly snapshot history (ordered by `report_month ASC`) | `MonthlySnapshotSeriesResponse` |
| `GET` | `/api/v1/projects/{project_id}/dossier` | Analytical monthly dossier row from `v_project_monthly_dossier` | `ProjectMonthlyDossierResponse` |

### Analytics & Alerts APIs (Phase 4B — Part 2)
| Method | Endpoint | Description | Response Schema |
|---|---|---|---|
| `GET` | `/api/v1/analytics/risk-rankings` | Ranked predictive ML risk scores (`selected_integrated_risk DESC`) | `PaginatedRiskRankingsResponse` |
| `GET` | `/api/v1/analytics/surveillance` | Ranked Pillar 2 execution stress scores (`execution_stress_index DESC`) | `PaginatedSurveillanceResponse` |
| `GET` | `/api/v1/alerts` | Stored operational system alerts (`created_at DESC, report_month DESC`) | `PaginatedAlertsResponse` |

---

## 9. Environment Variables

All configuration is loaded from environment variables or `backend/.env` using `pydantic-settings`:

| Variable Name | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection URI for Supabase |
| `API_HOST` | No | Host IP to bind server (default: `0.0.0.0`) |
| `API_PORT` | No | Port to bind server (default: `8000`) |
| `REDIS_URL` | No | Redis connection URI (optional; for future caching) |
| `JWT_SECRET` | No | Secret key for JWT signing (optional; for future auth) |

> [!CAUTION]
> `backend/.env` is local and private. It contains live credentials and is ignored by Git. **Never commit `.env` or paste credentials into any file.**

---

## 10. Local Setup

Using **Windows PowerShell**:

```powershell
# 1. Navigate to backend directory
cd TRIALHIDDEN\backend

# 2. Verify Python 3.11 installation
python --version

# 3. Create virtual environment (if not already present)
python -m venv .venv

# 4. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 5. Install dependencies
pip install -r requirements.txt
```

---

## 11. Running Backend

Start the development server with hot reload:

```powershell
.\.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Once running:
- Health Check: `http://127.0.0.1:8000/api/v1/health`
- Project Listing: `http://127.0.0.1:8000/api/v1/projects?page=1&page_size=20`
- Risk Rankings: `http://127.0.0.1:8000/api/v1/analytics/risk-rankings?page=1&page_size=20`
- Surveillance: `http://127.0.0.1:8000/api/v1/analytics/surveillance?page=1&page_size=20`
- Alerts: `http://127.0.0.1:8000/api/v1/alerts?page=1&page_size=20`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI Spec: `http://127.0.0.1:8000/openapi.json`

---

## 12. Running Tests

Run the complete test suite against the live database using `pytest`:

```powershell
.\.venv\Scripts\pytest.exe -v
```

**Verified Test Status**:
- **61 / 61 tests PASSED** in ~80 seconds.
- Zero failures, zero regressions across all 7 test modules.

---

## 13. Phase 5A — ML Integration Audit

### Audit Status
**COMPLETE (Audit & Discovery Only)**. No files inside `ai-ml/` were modified. No model retraining or DDL migrations were executed.

> [!IMPORTANT]
> **ML ONLINE INFERENCE: NOT IMPLEMENTED**.
> The FastAPI backend does NOT execute real-time single-project ML inference or import `joblib`/`scikit-learn` in request cycles. All production risk scores and surveillance indicators are pre-computed offline and persisted to Supabase PostgreSQL.

### Models Actually Found
1. **Primary Model — Operational Schedule Delay (`schedule_delay_3m`)**:
   - Algorithm: Random Forest (`RF_02`: 200 trees, max_depth=12, min_samples_leaf=5) with Sigmoid/Platt calibration.
   - Artifact: `ai-ml/ml/calibration_final/models/rf02_calibrated.pkl`.
   - OOT Performance: ROC-AUC = 0.9723, PR-AUC = 0.9722, Brier = 0.0389, F1@0.30 = 0.9638.
2. **Secondary Model 1 — Operational Cost Overrun State (`cost_overrun_state_3m`)**:
   - Algorithm: Random Forest (`class_weight='balanced'`: 200 trees, max_depth=12, min_samples_leaf=5).
   - Artifact: `ai-ml/ml/secondary_targets/selected_models/cost_overrun_state_3m/model.pkl`.
   - OOT Performance: ROC-AUC = 0.9895, PR-AUC = 0.9881, Brier = 0.0386.
3. **Secondary Model 2 — Schedule Revision Announcement (`schedule_revision_3m`)**:
   - Algorithm: Logistic Regression (L2 regularized, unweighted).
   - Artifact: `ai-ml/ml/secondary_targets/selected_models/schedule_revision_3m/model.pkl`.
   - OOT Performance: ROC-AUC = 0.8264, PR-AUC = 0.0519, Brier = 0.0176.
4. **Candidate B Integrated Risk Scoring Engine**:
   - Formulation: `selected_integrated_risk = 0.50 * schedule_delay_risk + 0.35 * cost_overrun_risk + 0.15 * schedule_revision_risk`.
   - Output: Risk Band (`LOW`, `MODERATE`, `HIGH`, `VERY_HIGH`) and Dominant Component (`Schedule Delay`, `Cost Overrun`, `Schedule Revision`).
   - Implementation: `ai-ml/ml/risk_engine/build_integrated_risk_score.py`.
5. **Operational Execution Surveillance (ESI)**:
   - **NOT an ML model**. ESI is a **deterministic, domain-calibrated operational index** computed from 5 point-in-time stress dimensions ($S_{\text{stag}}, S_{\text{vel}}, S_{\text{div}}, S_{\text{sched}}, S_{\text{rep}}$).
   - Implementation: `ai-ml/scripts/execution_risk/03_execution_stress_index.py`.

### Feature Contract Findings
- Total engineered universe: 79 point-in-time features.
- Active feature matrix $X$: Exactly **75 features** (71 numerical + 4 categorical).
  - 4 Categorical: `project_size_category`, `current_schedule_status_as_of_t`, `reporting_structure_version_t`, `table_source_t`.
  - 4 Raw dates excluded: `approval_start_date`, `original_completion_date`, `revised_doc_t`, `first_observed_month`.
  - 10 Cross-sectional context features (`state_mean_progress_t`, `agency_mean_cost_t`, etc.) require cross-project aggregation per month and are NOT stored as columns in `monthly_snapshots`.

### Output Contract & Database Mapping
- ML engine outputs map 1:1 to `ml_risk_scores` in Supabase PostgreSQL:
  - `schedule_delay_risk` $\to$ `ml_risk_scores.schedule_delay_risk`
  - `cost_overrun_risk` $\to$ `ml_risk_scores.cost_overrun_risk`
  - `schedule_revision_risk` $\to$ `ml_risk_scores.schedule_revision_risk`
  - `selected_integrated_risk` $\to$ `ml_risk_scores.selected_integrated_risk`
  - `risk_band` $\to$ `ml_risk_scores.risk_band`
  - `dominant_component` $\to$ `ml_risk_scores.dominant_component`
- Surveillance outputs map 1:1 to `execution_stress_scores`.

### Dependency Findings
- `backend/requirements.txt` has FastAPI, SQLAlchemy, psycopg2, pandas, pydantic-settings, pytest, httpx.
- `scikit-learn`, `joblib`, `scipy`, `lightgbm`, `xgboost`, `catboost`, `shap` are **NOT** installed in the backend virtual environment.

### Data Leakage Findings
- The offline feature pipeline strictly enforces point-in-time boundaries ($\le t$).
- Attempting on-the-fly single-project scoring inside FastAPI would risk leakage if future `revised_completion_date` values were fetched, or error out due to missing cross-sectional context aggregates.

### Integration Strategy Recommendation
- **Recommended: Option C (Batch ML Pipeline into PostgreSQL)**.
  - Periodic/monthly batch runner executes extraction, 75-feature construction, and model scoring in `ai-ml/`.
  - Results are bulk-loaded into `ml_risk_scores` and `execution_stress_scores`.
  - FastAPI backend remains pure, fast, lightweight, and strictly decoupled from heavy ML runtime dependencies.

### Integration Readiness Scores
1. Model Artifact Readiness: **9/10** (Frozen, calibrated joblib/pkl artifacts exist)
2. Inference Function Readiness: **4/10** (Only batch CSV scripts exist; no standalone function/class)
3. Feature Contract Readiness: **8/10** (75 features rigorously specified and audited)
4. Output Contract Readiness: **10/10** (Exact 1:1 schema mapping to PostgreSQL)
5. Database Mapping Readiness: **10/10** (15,769 ML rows and ESI rows pre-loaded)
6. Dependency Readiness: **3/10** (ML dependencies absent in backend venv)
7. Deployment Readiness: **8/10** (Decoupled read-only API is 100% production-ready)
- **Overall Integration Readiness: 7.4 / 10**

### Blockers
- No ML execution environment inside backend `.venv` (by design, keeping web API decoupled).
- Lack of a standalone, modular `score_month(report_month)` pipeline script in `ai-ml/`.

### Recommended Next Phase
**PHASE 5B — Batch Prediction Integration & Pipeline Ingestion** (or **PHASE 5B — Authentication & RBAC**).

---

## 14. Phase 5B-1 — Offline Batch Scoring Engine

### Overview
Phase 5B-1 created a modular, production-grade **offline batch scoring engine** around the existing frozen ML artifacts in `ai-ml/`. The scoring engine provides a clean, deterministic, and vector-accelerated inference interface that strictly enforces the 75-feature contract, point-in-time safety, lazy artifact loading, Candidate B evidence-weighted risk synthesis, and multi-component attribution.

### Engine Location & Structure
The batch scoring module is located in `ai-ml/ml/inference/`:
```text
ai-ml/ml/inference/
├── __init__.py           # Re-exports BatchScorer, contracts, exceptions, and constants
├── contracts.py          # Strict 75-feature contract, weights, bands, and custom exceptions
├── batch_scorer.py       # Modular, lazy-loaded BatchScorer implementation
└── test_batch_scorer.py  # Comprehensive unit & integration test suite (15/15 tests passing)
```

### Model Artifacts Used
All three models are loaded in read-only mode from frozen serialized joblib artifacts:
1. **Primary Schedule Delay**: `ai-ml/ml/calibration_final/models/rf02_calibrated.pkl`
   - Algorithm: Calibrated Random Forest (RF_02) with Sigmoid Calibrator.
   - Output: `schedule_delay_risk` $\in [0, 1]$.
2. **Secondary Cost Overrun State**: `ai-ml/ml/secondary_targets/selected_models/cost_overrun_state_3m/model.pkl`
   - Algorithm: Random Forest Balanced.
   - Output: `cost_overrun_risk` $\in [0, 1]$.
3. **Secondary Schedule Revision**: `ai-ml/ml/secondary_targets/selected_models/schedule_revision_3m/model.pkl`
   - Algorithm: Logistic Regression Unweighted.
   - Output: `schedule_revision_risk` $\in [0, 1]$.

### Input Contract
- **75 Certified Point-in-Time Features**:
  - **71 Numeric Features**: `original_cost_crore`, `project_age_months_t`, `planned_duration_months`, `original_cost_log`, `physical_progress_t`, `cumulative_expenditure_t`, `revised_cost_t`, `cost_escalation_pct_t`, `expenditure_ratio_pct_t`, `remaining_physical_progress_t`, `schedule_slippage_months_t`, `months_to_original_doc_t`, `months_to_revised_doc_t`, lags (1, 2, 3), velocities (1m, 3m, 6m), statistics, expenditure dynamics, stagnation metrics, revision frequencies, observation indicators, state/agency benchmarks, and focused cohort indicator.
  - **4 Categorical Features**: `project_size_category`, `current_schedule_status_as_of_t`, `reporting_structure_version_t`, `table_source_t`.
- **Validation Behavior**:
  - `scorer.validate_input(df)` strictly verifies that all 75 features are present.
  - If any required feature is absent, it immediately raises `MissingFeatureError` detailing the missing columns.
  - If input is empty or not a DataFrame, it raises `InvalidInputError`.
  - Point-in-time safety assumption: The batch scorer assumes its input DataFrame has already been constructed using the certified point-in-time feature engineering pipeline. Target columns (`schedule_delay_3m`, `cost_overrun_state_3m`, etc.) are explicitly ignored and never passed into the model matrix $X$.

### Output Contract
Each scored row produces a deterministic record with the following schema:
- `project_id`: Preserved from input metadata (if present).
- `report_month`: Preserved from `report_month` or mapped from `prediction_month` (if present).
- `schedule_delay_risk`: Calibrated probability of $\ge 3$-month schedule delay ($\in [0, 1]$).
- `cost_overrun_risk`: Probability of cost overrun state ($\in [0, 1]$).
- `schedule_revision_risk`: Probability of schedule revision event within 3 months ($\in [0, 1]$).
- `selected_integrated_risk`: Candidate B synthesis $= 0.50 \cdot \text{Delay} + 0.35 \cdot \text{Cost} + 0.15 \cdot \text{Revision}$.
- `risk_band`: Categorical risk classification based on fixed communication intervals:
  - `< 0.30` $\to$ `LOW`
  - `0.30` to `< 0.60` $\to$ `MODERATE`
  - `0.60` to `< 0.80` $\to$ `HIGH`
  - $\ge 0.80$ $\to$ `VERY_HIGH`
- `dominant_component`: Primary driver of risk among `['Schedule Delay', 'Cost Overrun', 'Schedule Revision']` via argmax over component contributions with deterministic tie-breaking.
- `schedule_contribution`: $0.50 \cdot \text{schedule\_delay\_risk}$.
- `cost_contribution`: $0.35 \cdot \text{cost\_overrun\_risk}$.
- `schedule_revision_contribution`: $0.15 \cdot \text{schedule\_revision\_risk}$.
- `model_version`: Constant string `"v1.0.0-rf02-calibrated"`.

### Model Loading & Determinism
- **Lazy Loading**: Model artifacts are not deserialized at import time; they are loaded lazily on first call to `score_batch()` or explicit `load_models()`.
- **Deterministic Output**: Pure vector operations guarantee exact bitwise reproducibility across runs. Verified against `integrated_risk_scores.csv` with 100% numerical match.

### ESI Status
- **Execution Stress Index (ESI)** is deterministic operational surveillance, completely decoupled from the machine learning batch scoring engine. ESI is NOT merged into `BatchScorer` and remains cleanly isolated.

### Architecture & Boundary Disclaimers
> [!WARNING]
> **DATABASE PERSISTENCE: NOT IMPLEMENTED**
> The batch scoring engine operates purely in-memory / offline. No database connections, queries, or writes are performed by `BatchScorer`.
>
> **FASTAPI INTEGRATION: NOT IMPLEMENTED**
> The batch scoring engine is not wired to FastAPI endpoints. ML inference dependencies (`scikit-learn`, `joblib`, `scipy`) remain strictly isolated to `ai-ml/.venv` and are NOT installed in `backend/.venv`.
>
> **AUTHENTICATION: NOT IMPLEMENTED**
> Authentication and authorization remain scheduled for subsequent phases.
>
> **MONTHLY AUTOMATED INGESTION: NOT IMPLEMENTED**
> Automated scheduling or cron jobs for feature building and prediction ingestion are not yet created.

---

## 15. Phase 5B-2 — Database Ingestion & Pipeline Orchestration

### Overview
Phase 5B-2 established an **offline database ingestion pipeline** that bridges the certified `BatchScorer` inference engine to the Supabase PostgreSQL database. The ingestion pipeline ingests raw point-in-time features, validates output contracts and numerical constraints, detects in-batch duplicate keys, and performs atomic, idempotent upserts into `ml_risk_scores` using SQLAlchemy 2.x and PostgreSQL's `ON CONFLICT (project_id, report_month) DO UPDATE`.

```text
feature snapshot CSV
        ↓
BatchScorer.score_batch()
        ↓
validated ML prediction records
        ↓
SQLAlchemy mapping (Decimal, Enums, UUID)
        ↓
idempotent PostgreSQL upsert (ON CONFLICT uq_ml_project_month DO UPDATE)
        ↓
ml_risk_scores
```

### Ingestion Script Location & CLI
The offline ingestion CLI is located at [`ai-ml/scripts/ingest_batch_predictions.py`](file:///c:/Users/shubh/OneDrive/Desktop/SIH2026_PS103/TRIALHIDDEN/ai-ml/scripts/ingest_batch_predictions.py).

Available options:
- `--feature-file`: Path to feature dataset CSV (default: `ai-ml/features/feature_dataset_v1.csv`).
- `--month`: Filter for specific reporting month (`YYYY-MM`).
- `--project-id`: Filter for specific project ID.
- `--limit`: Cap number of records to process.
- `--dry-run`: Full scoring, validation, and mapping without any database connection or write.
- `--rollback-test`: Live database verification executing the complete upsert inside an uncommitted transaction and explicitly rolling back (guaranteeing 0 net database mutations).
- `--database-url`: Optional database URL override; defaults to reading `DATABASE_URL` securely from `backend/.env` without logging credentials.

### Input Contract & Pre-Write Validation
Before executing database operations, `validate_prediction_dataframe()` performs strict pre-write checks:
1. **Contract Completeness**: Verifies all required prediction columns from `OUTPUT_COLUMNS` exist.
2. **In-Batch Duplicate Key Rejection**: Detects duplicate `(project_id, report_month)` composite keys inside the input batch. Raises `BatchDuplicateKeyError` and halts execution rather than silently picking arbitrary rows.
3. **Identifier Validity**: `project_id` must be non-empty string $\le 32$ characters; `report_month` must match regex `^\d{4}-(0[1-9]|1[0-2])$`.
4. **Numeric Integrity & Bounds**: All probability scores, integrated risks, and component contributions are validated against $[0.0, 1.0]$. Any `NaN`, `Inf`, or out-of-bounds value immediately triggers `BatchValidationError`.
5. **Enum Verification**: `risk_band` must match `RiskBandEnum` (`LOW`, `MODERATE`, `HIGH`, `VERY_HIGH`); `dominant_component` must match `DominantComponentEnum` (`Schedule Delay`, `Cost Overrun`, `Schedule Revision`).
6. **Model Version**: Must be a non-empty string $\le 32$ characters (`"v1.0.0-rf02-calibrated"`).

### Database Mapping & Upsert Strategy
- **ORM Model**: [`MLRiskScore`](file:///c:/Users/shubh/OneDrive/Desktop/SIH2026_PS103/TRIALHIDDEN/backend/app/models/risk.py) (`ml_risk_scores`).
- **Upsert Constraint**: Relies on the unique constraint `uq_ml_project_month UNIQUE (project_id, report_month)` verified in the live Supabase PostgreSQL database schema.
- **SQL Statement**:
  ```sql
  INSERT INTO ml_risk_scores (
      project_id, report_month, schedule_delay_risk, cost_overrun_risk,
      schedule_revision_risk, selected_integrated_risk, risk_band,
      dominant_component, schedule_contribution, cost_contribution,
      schedule_revision_contribution, model_version
  ) VALUES (...)
  ON CONFLICT (project_id, report_month)
  DO UPDATE SET
      schedule_delay_risk = EXCLUDED.schedule_delay_risk,
      cost_overrun_risk = EXCLUDED.cost_overrun_risk,
      schedule_revision_risk = EXCLUDED.schedule_revision_risk,
      selected_integrated_risk = EXCLUDED.selected_integrated_risk,
      risk_band = EXCLUDED.risk_band,
      dominant_component = EXCLUDED.dominant_component,
      schedule_contribution = EXCLUDED.schedule_contribution,
      cost_contribution = EXCLUDED.cost_contribution,
      schedule_revision_contribution = EXCLUDED.schedule_revision_contribution,
      model_version = EXCLUDED.model_version,
      scored_at = NOW();
  ```
- **Transaction Safety**: All database interactions are wrapped in an atomic session transaction. On any exception, the session immediately rolls back, masks connection credentials from error messages via `sanitize_error_message()`, and raises `DatabaseIngestionError`.

### Testing & Verification
- **Automated Ingestion Test Suite**: Located at [`ai-ml/scripts/test_ingest_batch_predictions.py`](file:///c:/Users/shubh/OneDrive/Desktop/SIH2026_PS103/TRIALHIDDEN/ai-ml/scripts/test_ingest_batch_predictions.py). 11 unit & integration tests passing (100% pass rate).
- **Total AI-ML Suite**: 26/26 tests passing across inference and ingestion modules.
- **Live Database Verification**: Non-destructive live verification executed against the Supabase PostgreSQL database using `--rollback-test --limit 1`. Verified query generation, constraint resolution, connection lifecycle, and transaction rollback with 0 net database mutations (15,769 rows preserved).
- **Backend Isolation**: Full 61-test backend regression suite passing in 86s with zero modifications to `backend/requirements.txt` or `backend/app/`.

### Architecture & Boundary Disclaimers
> [!WARNING]
> **FASTAPI TRIGGER: NOT IMPLEMENTED**
> Batch ingestion is an offline operational script designed for scheduled CLI or ETL execution. No FastAPI endpoint triggers or manages ingestion runs.
>
> **AUTHENTICATION: NOT IMPLEMENTED**
> Authentication and user management endpoints are scheduled for subsequent phases.
>
> **ESI INGESTION: NOT IMPLEMENTED**
> The Execution Stress Index (ESI) is an independent operational surveillance metric. It is strictly excluded from `ingest_batch_predictions.py` and `ml_risk_scores`.

---

## 16. Phase 5C-1 — Modular Execution Surveillance Engine

### Overview
Phase 5C-1 encapsulates the **Pillar 2 Operational Surveillance & Early Warning Engine** directly from longitudinal point-in-time project metrics ($t$). It is completely modularized inside `ai-ml/ml/surveillance/` and operates strictly on historical time-series data without looking at future evaluation windows or target variables.

### Surveillance Feature Contract (12 Features)
The engine strictly requires 12 point-in-time features ($t$) and rejects future/target columns:
1. `months_since_last_progress_increase_t` (integer/float $\ge 0$)
2. `stagnant_3m_t` (binary $\{0, 1\}$)
3. `remaining_physical_progress_t` (float $[0.0, 100.0]$)
4. `progress_velocity_3m_t` (float, fallback to 1m progress change)
5. `progress_change_1m_t` (float)
6. `schedule_slippage_months_t` (float $\ge 0$)
7. `months_to_original_doc_t` (float, negative indicates overdue)
8. `expenditure_ratio_pct_t` (float $\ge 0$)
9. `physical_progress_t` (float $[0.0, 100.0]$)
10. `observation_gap_flag_t` (binary $\{0, 1\}$)
11. `missing_physical_progress_t` (binary $\{0, 1\}$)
12. `schedule_revision_count_to_date_t` (integer/float $\ge 0$)

### 5 Core Stress Dimensions & Formulas
- **$S_{\text{stag}}$ (Physical Progress Stagnation Stress)**:
  $$\text{stag\_dur} = \min\left(\frac{\text{months\_stag}}{4.0}, 1.0\right)$$
  $$S_{\text{stag}} = 0.7 \cdot \text{stag\_dur} + 0.3 \cdot (\text{stag\_dur} \cdot \text{rem\_prog})$$
  - Flag: `flag_stag = 1` if `months_stag >= 3` OR `stagnant_3m_t == 1.0`.
- **$S_{\text{vel}}$ (Progress Velocity Deterioration Stress)**:
  Piecewise decay based on effective monthly velocity $v$:
  - $v \le 0.0 \implies 1.0$
  - $0.0 < v < 1.0 \implies 0.75 - 0.25 \cdot (v / 1.0)$
  - $1.0 \le v < 3.0 \implies 0.50 - 0.50 \cdot ((v - 1.0) / 2.0)$
  - $v \ge 3.0 \implies 0.0$
  - Flag: `flag_vel = 1` if $v < 0.5$.
- **$S_{\text{sched}}$ (Schedule Slippage & Proximity Stress)**:
  $$S_{\text{sched}} = 0.6 \cdot \min\left(\frac{\text{slippage}}{36.0}, 1.0\right) + 0.4 \cdot \min\left(\frac{-\text{months\_to\_doc}}{24.0}, 1.0\right) \cdot \mathbb{I}_{\text{overdue}}$$
  - Flag: `flag_sched = 1` if `slippage >= 12.0` OR `months_to_doc < -6.0`.
- **$S_{\text{div}}$ (Expenditure / Progress Divergence Stress)**:
  $$\Delta_{\text{div}} = \text{exp\_ratio} - \text{phys\_prog}$$
  $$S_{\text{div}} = \begin{cases} 0.0, & \Delta_{\text{div}} \le 0.0 \\ \min\left(\frac{\Delta_{\text{div}}}{75.0}, 1.0\right), & \Delta_{\text{div}} > 0.0 \end{cases}$$
  - Flag: `flag_div = 1` if $\Delta_{\text{div}} > 25.0$.
- **$S_{\text{rep}}$ (Observation & Reporting Quality Stress)**:
  $$S_{\text{rep}} = 0.4 \cdot \text{obs\_gap} + 0.3 \cdot \text{miss\_prog} + 0.3 \cdot \min\left(\frac{\text{rev\_count}}{3.0}, 1.0\right)$$
  - Flag: `flag_rep = 1` if `obs_gap == 1` OR `miss_prog == 1` OR `rev_count >= 2`.

### Composite Execution Stress Index (ESI) & Weights
Domain-calibrated weighted synthesis:
$$\text{ESI} = 0.30 \cdot S_{\text{stag}} + 0.25 \cdot S_{\text{vel}} + 0.20 \cdot S_{\text{div}} + 0.15 \cdot S_{\text{sched}} + 0.10 \cdot S_{\text{rep}}$$
Rounded to 4 decimal places. Version identifier: `"v1.0.0-esi-5dim"`.

### Canonical Alert Tiers
- **`NOMINAL`**: $\text{ESI} < 0.35$
- **`WATCH`**: $0.35 \le \text{ESI} < 0.55$
- **`ATTENTION`**: $0.55 \le \text{ESI} < 0.75$
- **`HIGH_PRIORITY`**: $\text{ESI} \ge 0.75$

### Dominant Stressor Attribution & Deterministic Tie-Breaking
Attributed to the dimension with the largest weighted contribution ($w_i = W_i \cdot S_i$). In the event of a tie, the tie breaks strictly according to canonical priority:
1. `Physical Progress Stagnation`
2. `Progress Velocity Collapse`
3. `Expenditure Divergence`
4. `Schedule Slippage Debt`
5. `Reporting Friction`

### Prescriptive Action Priority Hierarchy
1. **Priority 1 (Compound Escalation)**: $\text{ESI} \ge 0.75$ and `total_stress_flags >= 3` $\to$ `INTER_MINISTERIAL_COMMITTEE_ESCALATION`
2. **Priority 2 (Stagnation)**: $S_{\text{stag}} \ge 0.75$ or `flag_stag == 1` $\to$ `SITE_OBSTACLE_AUDIT`
3. **Priority 3 (Divergence)**: $S_{\text{div}} \ge 0.75$ or `flag_div == 1` $\to$ `FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT`
4. **Priority 4 (Velocity)**: $S_{\text{vel}} \ge 0.75$ or `flag_vel == 1` $\to$ `RESOURCE_MOBILIZATION_DIRECTIVE`
5. **Priority 5 (Schedule)**: $S_{\text{sched}} \ge 0.75$ or `flag_sched == 1` $\to$ `CRITICAL_PATH_RECALIBRATION`
6. **Priority 6 (Reporting)**: $S_{\text{rep}} \ge 0.75$ or `flag_rep == 1` $\to$ `DATA_COMPLIANCE_DIRECTIVE`
7. **Priority 7 (Dominant Stressor Fallback)**:
   - `Expenditure Divergence` $\to$ `FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT`
   - `Progress Velocity Collapse` $\to$ `RESOURCE_MOBILIZATION_DIRECTIVE`
   - `Schedule Slippage Debt` $\to$ `CRITICAL_PATH_RECALIBRATION`
   - `Reporting Friction` $\to$ `DATA_COMPLIANCE_DIRECTIVE`
   - Default $\to$ `SITE_OBSTACLE_AUDIT`

### Verification & Testing
- **Test Suite**: `ai-ml/ml/surveillance/test_surveillance_engine.py` covering all 22 required minimum test cases (100% pass rate).
- **Full AI-ML Suite**: 48/48 tests passing (15 BatchScorer + 11 Ingestion CLI + 22 Surveillance Engine).
- **Backend Isolation**: Full 61-test backend regression suite passing with zero dependencies added to `backend/requirements.txt`.
- **Numerical Equivalence**: 0.000000 maximum difference verified against all 15,769 reference rows and live PostgreSQL seed values in `execution_stress_scores`.

### Disclaimers
> [!WARNING]
> **FASTAPI INTEGRATION: NOT IMPLEMENTED**
> ESI computation remains an offline, modular intelligence service. No FastAPI endpoint triggers live calculation.
>
> **DATABASE INGESTION: NOT IMPLEMENTED**
> Database persistence for newly computed ESI scores will be implemented as an offline CLI pipeline in Phase 5C-2.

---

## 17. Phase 5C-2 — Execution Surveillance Database Ingestion Pipeline

### Overview
Phase 5C-2 implements the offline batch ingestion pipeline connecting the modular [`ExecutionSurveillanceEngine`](file:///c:/Users/shubh/OneDrive/Desktop/SIH2026_PS103/TRIALHIDDEN/ai-ml/ml/surveillance/surveillance_engine.py) to the central Supabase PostgreSQL database table [`execution_stress_scores`](file:///c:/Users/shubh/OneDrive/Desktop/SIH2026_PS103/TRIALHIDDEN/backend/app/models/execution.py).

### Ingestion Pipeline Architecture
```text
feature_dataset_v1.csv
        ↓
ExecutionSurveillanceEngine.compute_scores()
        ↓
ESI structured scores & directives
        ↓
validate_surveillance_dataframe()
  - 12-feature input contract check
  - in-batch duplicate key rejection
  - score bounds [0.0, 1.0] (no NaN/Inf)
  - operational flags in {0, 1}
  - total_stress_flags in [0, 5] and matching sum
  - canonical ESI tier / stressor / action enum validation
  - version validation: "v1.0.0-esi-5dim"
  - Decimal(6,4) conversion
        ↓
verify_project_foreign_keys()
  - validates project_id in master projects table
        ↓
upsert_execution_stress_scores()
  - PostgreSQL ON CONFLICT (project_id, report_month) DO UPDATE
        ↓
PostgreSQL execution_stress_scores table
```

### Script & CLI Options
The ingestion pipeline is implemented in [`ai-ml/scripts/ingest_surveillance_scores.py`](file:///c:/Users/shubh/OneDrive/Desktop/SIH2026_PS103/TRIALHIDDEN/ai-ml/scripts/ingest_surveillance_scores.py):
- `--feature-file`: Path to feature dataset CSV (default: `ai-ml/features/feature_dataset_v1.csv`). Reads `project_id` with `dtype=str` to preserve leading zeroes.
- `--month`: Optional report month filter (`YYYY-MM`), e.g. `2026-03`.
- `--project-id`: Optional project ID filter, e.g. `060100093`.
- `--limit`: Optional maximum number of rows to evaluate and ingest.
- `--dry-run`: Computes and validates surveillance scores without opening a database connection or writing data.
- `--rollback-test`: Executes the full database upsert inside an uncommitted transaction and explicitly rolls back, guaranteeing zero persistent database changes.
- `--database-url`: Optional explicit database URL override (otherwise read securely from environment or `backend/.env`).
- `--verify-reference`: Compares freshly computed scores against `experiments/execution_risk/execution_stress_scores.csv` if present.

### Database Target & Upsert Strategy
- **Target Table**: `execution_stress_scores`.
- **Natural Composite Key**: `(project_id, report_month)`.
- **Constraint**: `uq_esi_project_month UNIQUE (project_id, report_month)`.
- **Idempotent SQL Statement**:
  ```sql
  INSERT INTO execution_stress_scores (
      project_id, report_month,
      s_stag, s_vel, s_div, s_sched, s_rep,
      flag_stag, flag_vel, flag_div, flag_sched, flag_rep,
      total_stress_flags, execution_stress_index, esi_tier,
      dominant_stressor, suggested_action, execution_index_version,
      evaluated_at
  ) VALUES (...)
  ON CONFLICT (project_id, report_month)
  DO UPDATE SET
      s_stag = EXCLUDED.s_stag,
      s_vel = EXCLUDED.s_vel,
      s_div = EXCLUDED.s_div,
      s_sched = EXCLUDED.s_sched,
      s_rep = EXCLUDED.s_rep,
      flag_stag = EXCLUDED.flag_stag,
      flag_vel = EXCLUDED.flag_vel,
      flag_div = EXCLUDED.flag_div,
      flag_sched = EXCLUDED.flag_sched,
      flag_rep = EXCLUDED.flag_rep,
      total_stress_flags = EXCLUDED.total_stress_flags,
      execution_stress_index = EXCLUDED.execution_stress_index,
      esi_tier = EXCLUDED.esi_tier,
      dominant_stressor = EXCLUDED.dominant_stressor,
      suggested_action = EXCLUDED.suggested_action,
      execution_index_version = EXCLUDED.execution_index_version,
      evaluated_at = NOW();
  ```
- **Foreign Key Safety**: Before upsert, `verify_project_foreign_keys()` queries the `projects` table to ensure every `project_id` in the batch exists. Missing IDs raise `MissingProjectError` and trigger transaction rollback.
- **Precision**: Scores are stored as `NUMERIC(6,4)` using `to_decimal_4()` to avoid floating point inaccuracies.

### Testing & Verification
- **Automated Ingestion Test Suite**: Located at [`ai-ml/scripts/test_ingest_surveillance_scores.py`](file:///c:/Users/shubh/OneDrive/Desktop/SIH2026_PS103/TRIALHIDDEN/ai-ml/scripts/test_ingest_surveillance_scores.py). 41 unit & integration tests passing (100% pass rate).
- **Total AI-ML Suite**: 89/89 tests passing across inference, batch prediction ingestion, surveillance engine, and surveillance ingestion.
- **Backend Isolation**: Full 61-test backend regression suite passing with zero dependencies added to `backend/requirements.txt`.
- **Live Database Verification**: Verified against live Supabase PostgreSQL database using `--rollback-test --limit 1`:
  - `count_before`: 15,769
  - `count_after`: 15,769
  - Test project row values remained 100% bit-identical.
  - Zero persistent mutations occurred.

### Disclaimers
> [!WARNING]
> **FASTAPI INTEGRATION: NOT IMPLEMENTED**
> ESI database ingestion is an offline operational pipeline designed for batch processing. No FastAPI endpoint triggers or manages ingestion runs.
>
> **AUTHENTICATION: NOT IMPLEMENTED**
> Authentication and user management endpoints are scheduled for subsequent phases.

---

## 18. Phase 5D — FastAPI Intelligence Integration

### 18.1 Overview & Architecture
Phase 5D exposes precomputed predictive machine learning risk scores and operational Execution Stress Index (ESI) surveillance intelligence from Supabase PostgreSQL through a clean, frontend-ready FastAPI layer.

```text
Offline Batch Scoring (BatchScorer)           Offline Surveillance (ExecutionSurveillanceEngine)
             ↓                                                  ↓
   PostgreSQL: ml_risk_scores                       PostgreSQL: execution_stress_scores
             └──────────────────────┬───────────────────────────┘
                                    ↓
                 FastAPI Backend (/api/v1) [READ-ONLY]
                    ├── /projects/{project_id}/intelligence
                    ├── /analytics/summary
                    ├── /analytics/risk-rankings
                    ├── /analytics/surveillance
                    └── /alerts
                                    ↓
                         Frontend Web Applications
```

> [!IMPORTANT]
> **CRITICAL ARCHITECTURAL BOUNDARIES**:
> - **ML INFERENCE INSIDE FASTAPI: NOT IMPLEMENTED**.
> - **ESI COMPUTATION INSIDE FASTAPI: NOT IMPLEMENTED**.
> - **FASTAPI READS PRECOMPUTED INTELLIGENCE FROM POSTGRESQL**.
> - Backend runtime environment has ZERO dependencies on `scikit-learn`, `joblib`, or `scipy`.
> - All endpoints are 100% READ-ONLY (zero `INSERT`, `UPDATE`, `DELETE`, or DDL operations).

### 18.2 Endpoints Summary

| Method | Endpoint | Description | Data Sources |
|---|---|---|---|
| `GET` | `/api/v1/projects/{project_id}/intelligence` | Single-project unified intelligence dossier | `projects`, `monthly_snapshots`, `ml_risk_scores`, `execution_stress_scores`, `system_alerts`, `v_project_monthly_dossier` |
| `GET` | `/api/v1/analytics/summary` | Portfolio-level intelligence summary & distributions | `projects`, `monthly_snapshots`, `ml_risk_scores`, `execution_stress_scores`, `system_alerts` |
| `GET` | `/api/v1/analytics/risk-rankings` | Paginated predictive ML risk score rankings | `ml_risk_scores` |
| `GET` | `/api/v1/analytics/surveillance` | Paginated Pillar 2 operational ESI scores | `execution_stress_scores` |
| `GET` | `/api/v1/alerts` | Paginated operational system alerts | `system_alerts` |
| `GET` | `/api/v1/projects` | Paginated master project catalog | `projects` |
| `GET` | `/api/v1/projects/{project_id}` | Detailed project metadata | `projects` |
| `GET` | `/api/v1/projects/{project_id}/snapshots` | Monthly snapshot time-series | `monthly_snapshots` |
| `GET` | `/api/v1/projects/{project_id}/dossier` | Analytical lag-derived dossier | `v_project_monthly_dossier` |
| `GET` | `/api/v1/health` | Service and database connectivity health | PostgreSQL `SELECT 1` |

### 18.3 Endpoint Details: Unified Project Intelligence
- **Route**: `GET /api/v1/projects/{project_id}/intelligence`
- **Response Model**: `ProjectIntelligenceResponse`
- **Semantics**:
  - Automatically queries the latest available observation for each component independently (`ORDER BY report_month DESC LIMIT 1`).
  - Does not assume snapshot, ML, and ESI months are identical.
  - Queries the most recent stored system alerts for the project (`ORDER BY created_at DESC, report_month DESC, alert_id ASC LIMIT 20`).
  - **Null Safety**: If a project has no risk score or no surveillance score, returns `null` for that component (and `[]` for alerts) rather than failing the entire request.
  - Returns `404 NOT FOUND` if the project itself does not exist in `projects`.

### 18.4 Endpoint Details: Portfolio Summary
- **Route**: `GET /api/v1/analytics/summary`
- **Query Parameter**: `report_month` (optional, format `YYYY-MM`).
- **Response Model**: `PortfolioSummaryResponse`
- **Semantics**:
  - Dynamically computes `total_projects` and `active_projects` from `projects`.
  - Dynamically evaluates `latest_snapshot_month` via `MAX(report_month)` on `monthly_snapshots`.
  - If `report_month` is omitted, dynamically determines the target intelligence epoch via `MAX(report_month)` on `ml_risk_scores`.
  - Calculates `scored_projects`, `risk_band_distribution` (LOW, MODERATE, HIGH, VERY_HIGH), and `esi_tier_distribution` (NOMINAL, WATCH, ATTENTION, HIGH_PRIORITY) for the target epoch using fast indexed SQL aggregations.
  - Returns alert counts broken down by severity and status.
  - **Zero Hardcoding**: All counts, months, and distributions are derived dynamically from database queries.

### 18.5 CORS Configuration
- Configured in `app/core/config.py` and registered via FastAPI `CORSMiddleware` in `app/main.py`.
- **Environment Variable**: `CORS_ORIGINS` (comma-separated or JSON list).
- Default origins: `http://localhost:3000`, `http://localhost:5173`, `http://127.0.0.1:3000`, `http://127.0.0.1:5173`.
- **Safety Guarantee**: `allow_credentials` is automatically set to `False` if wildcard `*` is specified in origins, preventing insecure cross-origin credential exposures.

### 18.6 Verification Results
- **Backend Test Suite**: **72/72 tests passing** (61 existing baseline + 11 new Phase 5D tests).
- **AI-ML Test Suite**: **89/89 tests passing** (BatchScorer, ML ingestion, SurveillanceEngine, ESI ingestion).
- **Live DB Zero-Mutation Verification**: Confirmed before and after API smoke testing:
  - `projects`: 2,741 -> 2,741 (unchanged)
  - `monthly_snapshots`: 21,555 -> 21,555 (unchanged)
  - `ml_risk_scores`: 15,769 -> 15,769 (unchanged)
  - `execution_stress_scores`: 15,769 -> 15,769 (unchanged)
  - `system_alerts`: 0 -> 0 (unchanged)

---

## 19. Security Rules

1. **Protect `.env`**: Never commit `backend/.env`, never stage it, and never print its contents.
2. **Sanitize Logs & Exceptions**: Never log or return `DATABASE_URL`, connection strings, passwords, or raw database connection error tracebacks that may contain host or user information.
3. **Zero Hardcoded Secrets**: Keep all credentials strictly within environment variables.
4. **No Unapproved Schema Changes**: Never modify `database/schema.sql`, migrations, or remote Supabase schema without explicit review and approval.
5. **Read-Only Test Suite**: Tests must never perform destructive writes, updates, deletes, or table creations on the live database.

---

## 20. Known Limitations

The following items are intentional boundaries of the current development phase (not bugs):
- **ML Online Inference**: Real-time single-project feature extraction and ML inference are not implemented in FastAPI; predictions are pre-computed in batch and served from PostgreSQL.
- **Authentication**: JWT issuance, login routes, password hashing verification, and user management endpoints are not yet implemented.
- **Redis Cache**: Redis caching layer is planned but not yet connected.
- **Frontend Dashboard**: The React web dashboard is not yet connected to the backend API.

---

## 21. Phase History

| Phase | Status | What Was Completed |
|---|---|---|
| **Phase 1** | Complete | FastAPI foundation, structured directory layout, `pydantic-settings` config, `/api/v1/health` endpoint, `/docs` Swagger, `/openapi.json`, gitignore protection, and baseline unit tests. |
| **Phase 2A** | Complete | Comprehensive audit of Supabase PostgreSQL schema, migrations `001`–`003`, and table inventory. Connection architecture design. |
| **Phase 2B** | Complete | Live Supabase connection, URL scheme normalization, connection pooling (`pool_pre_ping=True`), `get_db` FastAPI dependency, database-aware health check, and non-destructive `SELECT 1` tests. |
| **Phase 3A** | Complete | Table-to-model mapping design, PostgreSQL enum analysis, foreign key and cascade design, nullability review for relaxed fields, and view identity analysis. |
| **Phase 3B** | Complete | Complete SQLAlchemy ORM model layer (9 models + 1 view model + 9 enums), composite PK handling, read-only view event hooks, and 20 passing verification tests. |
| **Phase 4A** | Complete | Pydantic v2 API schema layer (8 modules, 9 response/series schemas) with ORM serialization (`from_attributes=True`), decimal preservation, exact enum serialization, and 12 non-destructive schema validation tests. |
| **Phase 4B — Part 1** | Complete | Read-only project business APIs (`/api/v1/projects`, `/{id}`, `/{id}/snapshots`, `/{id}/dossier`) with repository, service, and router layers, bounded pagination, filters, and 12 integration tests. |
| **Phase 4B — Part 2** | Complete | Read-only analytics and alert APIs (`/api/v1/analytics/risk-rankings`, `/api/v1/analytics/surveillance`, `/api/v1/alerts`) with deterministic ordering, custom enum filters, empty table safety, and 17 integration tests (61 total tests passing). |
| **Phase 5A** | Complete | Comprehensive technical audit of `ai-ml/` pipeline, feature contracts, model artifacts, ESI surveillance architecture, dependencies, and integration boundaries. |
| **Phase 5B-1** | Complete | Modular offline batch scoring engine (`ai-ml/ml/inference/`) around frozen ML models, strict 75-feature validation, Candidate B synthesis, 15/15 passing unit/integration tests, and exact reference equivalence. |
| **Phase 5B-2** | Complete | Offline database ingestion CLI (`ai-ml/scripts/ingest_batch_predictions.py`), idempotent PostgreSQL upsert (`uq_ml_project_month`), in-batch duplicate key rejection, 11 ingestion tests, and non-destructive live DB rollback verification. |
| **Phase 5C-1** | Complete | Modular execution surveillance engine (`ai-ml/ml/surveillance/`), 5-dimensional ESI formulation, canonical tiers, deterministic dominant stressor tie-breaking, prescriptive action logic matrix, 22 unit tests, and exact reference equivalence across 15,769 records. |
| **Phase 5C-2** | Complete | Offline execution surveillance ingestion CLI (`ai-ml/scripts/ingest_surveillance_scores.py`), idempotent PostgreSQL upsert (`uq_esi_project_month`), foreign key validation, 41 unit tests, and non-destructive live DB rollback verification (15,769 rows). |
| **Phase 5D** | Complete | Read-only FastAPI integration of stored ML + ESI intelligence (`/projects/{id}/intelligence`, `/analytics/summary`), environment CORS policy, 72 backend tests passing, 89 AI-ML regression tests passing, live DB verified. |

---

## 22. Developer Handoff

### If you are continuing this project

1. **Activate Virtual Environment**: Always activate `backend/.venv` before running any commands (`.\.venv\Scripts\Activate.ps1`).
2. **Never Modify `backend/.env`**: Treat `.env` as read-only. It already contains working Supabase credentials.
3. **Run Tests Before Making Changes**: Always run `pytest -v` before writing new code to verify that all 61 tests pass.
4. **Read `database/schema.sql`**: Always review the source schema and migrations `001`–`003` before proposing any data model changes.
5. **Treat Supabase as Source of Truth**: Never execute `Base.metadata.create_all()` or alter database tables from the backend without team consensus.
6. **Do Not Modify `ai-ml/`**: Keep backend changes strictly within `backend/` unless explicitly tasked with ML integration.
7. **Keep README Updated**: Update this `README.md` after completing each subsequent phase.
8. **Update Phase Status**: Keep the Phase table in Section 2 and Section 16 updated as the backend evolves.
