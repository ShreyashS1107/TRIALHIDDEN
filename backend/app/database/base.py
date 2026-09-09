from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy 2.x ORM models.
    Application models will inherit from this base in subsequent phases.
    """
    pass
