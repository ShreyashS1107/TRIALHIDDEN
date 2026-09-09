from decimal import Decimal
import inspect as py_inspect
import pytest
from sqlalchemy import String, inspect, text
from sqlalchemy.types import Numeric

from app.database.base import Base
from app.database.session import engine, get_db
from app.models import (
    AlertSeverityEnum,
    AlertSourceEnum,
    AlertStatusEnum,
    CompletedProject,
    DataAnomalyLog,
    DominantComponentEnum,
    DominantStressorEnum,
    EsiTierEnum,
    ExecutionStressScore,
    MLRiskScore,
    MonthlySnapshot,
    NewlyAddedProject,
    PrescriptiveActionEnum,
    Project,
    ProjectMonthlyDossier,
    RiskBandEnum,
    SystemAlert,
    User,
    UserRoleEnum,
)

CORE_MODELS = [
    Project,
    MonthlySnapshot,
    MLRiskScore,
    ExecutionStressScore,
    CompletedProject,
    NewlyAddedProject,
    DataAnomalyLog,
    SystemAlert,
    User,
]


def test_a_all_expected_tables_exist():
    """A. Verify all expected tables exist in the database."""
    inspector = inspect(engine)
    db_tables = inspector.get_table_names()
    for model in CORE_MODELS:
        assert model.__tablename__ in db_tables, f"Table {model.__tablename__} not found in database."


def test_b_model_tablenames_match_database():
    """B. Verify model __tablename__ values match tables and views in database."""
    inspector = inspect(engine)
    db_tables = set(inspector.get_table_names())
    db_views = set(inspector.get_view_names())

    for model in CORE_MODELS:
        assert model.__tablename__ in db_tables

    assert ProjectMonthlyDossier.__tablename__ in db_views, (
        f"View {ProjectMonthlyDossier.__tablename__} not found in database views."
    )


def test_c_primary_key_mappings():
    """C. Verify primary key mappings are correct."""
    inspector = inspect(engine)
    for model in CORE_MODELS:
        model_pk_cols = [c.name for c in inspect(model).primary_key]
        if model is ExecutionStressScore:
            # ExecutionStressScore uses composite PK for ORM identity
            assert set(model_pk_cols) == {"project_id", "report_month"}
        else:
            db_pk = inspector.get_pk_constraint(model.__tablename__)
            assert set(model_pk_cols) == set(db_pk["constrained_columns"])


def test_d_foreign_key_mappings():
    """D. Verify foreign key mappings to projects(project_id) with CASCADE."""
    fk_models = [
        MonthlySnapshot,
        MLRiskScore,
        ExecutionStressScore,
        DataAnomalyLog,
        SystemAlert,
    ]
    inspector = inspect(engine)
    for model in fk_models:
        fks = inspector.get_foreign_keys(model.__tablename__)
        project_fks = [
            fk for fk in fks
            if fk["referred_table"] == "projects"
            and fk["referred_columns"] == ["project_id"]
        ]
        assert len(project_fks) > 0, f"No FK to projects found on {model.__tablename__}"
        assert project_fks[0]["options"].get("ondelete") == "CASCADE"


def test_e_f_column_names_and_nullability():
    """E & F. Verify column names and nullability match the database."""
    inspector = inspect(engine)
    for model in CORE_MODELS:
        db_cols = {c["name"]: c for c in inspector.get_columns(model.__tablename__)}
        mapper = inspect(model)
        for col_prop in mapper.column_attrs:
            col = col_prop.columns[0]
            assert col.name in db_cols, f"Column {col.name} missing from table {model.__tablename__}"
            db_col = db_cols[col.name]
            assert col.nullable == db_col["nullable"], (
                f"Nullability mismatch on {model.__tablename__}.{col.name}: "
                f"ORM={col.nullable} vs DB={db_col['nullable']}"
            )


def test_g_enum_values_match_database():
    """G. Verify PostgreSQL enum values match Python enum values."""
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT t.typname, e.enumlabel
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
            WHERE n.nspname = 'public'
            ORDER BY t.typname, e.enumsortorder;
        """))
        db_enums = {}
        for typname, enumlabel in res:
            db_enums.setdefault(typname, []).append(enumlabel)

    enum_mappings = [
        ("risk_band_enum", RiskBandEnum),
        ("dominant_component_enum", DominantComponentEnum),
        ("esi_tier_enum", EsiTierEnum),
        ("dominant_stressor_enum", DominantStressorEnum),
        ("prescriptive_action_enum", PrescriptiveActionEnum),
        ("alert_severity_enum", AlertSeverityEnum),
        ("alert_source_enum", AlertSourceEnum),
        ("alert_status_enum", AlertStatusEnum),
        ("user_role_enum", UserRoleEnum),
    ]

    for type_name, python_enum in enum_mappings:
        assert type_name in db_enums, f"PostgreSQL enum {type_name} not found in database."
        expected_values = db_enums[type_name]
        actual_values = [e.value for e in python_enum]
        assert set(actual_values) == set(expected_values), (
            f"Enum mismatch for {type_name}: expected {expected_values}, got {actual_values}"
        )


def test_h_numeric_columns_map_to_numeric():
    """H. Verify numeric columns map to Numeric/Decimal."""
    assert isinstance(Project.original_cost_crore.property.columns[0].type, Numeric)
    assert isinstance(MonthlySnapshot.revised_cost_crore.property.columns[0].type, Numeric)
    assert isinstance(MonthlySnapshot.physical_progress_percent.property.columns[0].type, Numeric)
    assert isinstance(MLRiskScore.schedule_delay_risk.property.columns[0].type, Numeric)
    assert isinstance(MLRiskScore.selected_integrated_risk.property.columns[0].type, Numeric)
    assert isinstance(ExecutionStressScore.execution_stress_index.property.columns[0].type, Numeric)
    assert isinstance(ExecutionStressScore.s_stag.property.columns[0].type, Numeric)


def test_i_month_fields_remain_string_seven():
    """I. Verify month fields remain String(7)."""
    month_columns = [
        Project.approval_start_date,
        Project.original_completion_date,
        MonthlySnapshot.report_month,
        MonthlySnapshot.revised_completion_date,
        MLRiskScore.report_month,
        ExecutionStressScore.report_month,
        CompletedProject.actual_completion_date,
        CompletedProject.report_month,
        NewlyAddedProject.approval_start_date,
        NewlyAddedProject.original_completion_date,
        NewlyAddedProject.report_month,
        SystemAlert.report_month,
        DataAnomalyLog.report_month,
    ]
    for col_prop in month_columns:
        col = col_prop.property.columns[0]
        assert isinstance(col.type, String), f"{col} is not a String type"
        assert col.type.length == 7, f"{col} length is {col.type.length}, expected 7"


def test_j_no_create_all_executed():
    """J. Verify no model or test calls Base.metadata.create_all()."""
    import app.models
    # Ensure Base metadata has not been called with create_all
    import pathlib
    backend_dir = pathlib.Path(__file__).resolve().parent.parent
    for py_file in backend_dir.glob("app/**/*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "create_all" not in content, f"create_all() found in {py_file}"


def test_k_project_relationships_configured():
    """K. Verify Project relationships are configured."""
    mapper = inspect(Project)
    rel_names = {r.key for r in mapper.relationships}
    expected_rels = {
        "monthly_snapshots",
        "ml_risk_scores",
        "execution_stress_scores",
        "system_alerts",
        "anomalies",
    }
    assert expected_rels.issubset(rel_names), f"Missing relationships on Project: {expected_rels - rel_names}"


def test_l_limit_one_read_query_for_all_tables():
    """L. Execute a non-destructive LIMIT 1 SELECT query for each table."""
    db_gen = get_db()
    session = next(db_gen)
    try:
        for model in CORE_MODELS:
            result = session.query(model).limit(1).all()
            assert isinstance(result, list)
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


def test_m_limit_one_read_query_for_analytical_view():
    """M. Execute a non-destructive LIMIT 1 SELECT query for v_project_monthly_dossier."""
    db_gen = get_db()
    session = next(db_gen)
    try:
        result = session.query(ProjectMonthlyDossier).limit(1).all()
        assert isinstance(result, list)
        if result:
            row = result[0]
            assert row.snapshot_id is not None
            assert row.project_id is not None
            assert row.report_month is not None
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


def test_m_view_read_only_enforced():
    """Verify that attempting to mutate ProjectMonthlyDossier raises an error."""
    instance = ProjectMonthlyDossier()
    db_gen = get_db()
    session = next(db_gen)
    try:
        session.add(instance)
        with pytest.raises(RuntimeError, match="read-only"):
            session.flush()
    finally:
        session.rollback()
        try:
            next(db_gen)
        except StopIteration:
            pass
