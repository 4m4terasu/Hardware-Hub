from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreateRequest(BaseModel):
    email: str
    password: str
    is_admin: bool = False


class UserRead(BaseModel):
    id: int
    email: str
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)