import enum


class RiskBandEnum(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class DominantComponentEnum(str, enum.Enum):
    SCHEDULE_DELAY = "Schedule Delay"
    COST_OVERRUN = "Cost Overrun"
    SCHEDULE_REVISION = "Schedule Revision"


class EsiTierEnum(str, enum.Enum):
    NOMINAL = "NOMINAL"
    WATCH = "WATCH"
    ATTENTION = "ATTENTION"
    HIGH_PRIORITY = "HIGH_PRIORITY"


class DominantStressorEnum(str, enum.Enum):
    PROGRESS_VELOCITY_COLLAPSE = "Progress Velocity Collapse"
    PHYSICAL_PROGRESS_STAGNATION = "Physical Progress Stagnation"
    EXPENDITURE_DIVERGENCE = "Expenditure Divergence"
    SCHEDULE_SLIPPAGE_DEBT = "Schedule Slippage Debt"
    REPORTING_FRICTION = "Reporting Friction"


class PrescriptiveActionEnum(str, enum.Enum):
    SITE_OBSTACLE_AUDIT = "SITE_OBSTACLE_AUDIT"
    FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT = "FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT"
    RESOURCE_MOBILIZATION_DIRECTIVE = "RESOURCE_MOBILIZATION_DIRECTIVE"
    CRITICAL_PATH_RECALIBRATION = "CRITICAL_PATH_RECALIBRATION"
    DATA_COMPLIANCE_DIRECTIVE = "DATA_COMPLIANCE_DIRECTIVE"
    INTER_MINISTERIAL_COMMITTEE_ESCALATION = "INTER_MINISTERIAL_COMMITTEE_ESCALATION"


class AlertSeverityEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertSourceEnum(str, enum.Enum):
    ML_ENGINE = "ML_ENGINE"
    RULE_ENGINE = "RULE_ENGINE"
    EXECUTION_SURVEILLANCE = "EXECUTION_SURVEILLANCE"
    PREDICTIVE_ML = "PREDICTIVE_ML"


class AlertStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class UserRoleEnum(str, enum.Enum):
    MOSPI_ADMIN = "MOSPI_ADMIN"
    NODAL_OFFICER = "NODAL_OFFICER"
    PUBLIC_VIEWER = "PUBLIC_VIEWER"
