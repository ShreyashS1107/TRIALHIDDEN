from pydantic import Field
from app.schemas.common import BaseSchema

class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    role: str

class LoginRequest(BaseSchema):
    email: str
    password: str
