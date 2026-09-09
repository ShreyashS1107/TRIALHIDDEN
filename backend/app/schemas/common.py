from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Base Pydantic v2 configuration schema for the SIH26103 API layer.
    Enables ORM attribute extraction (from_attributes=True) and clean serialization.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
