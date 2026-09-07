from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str | None
    display_name: str | None
    avatar_url: str | None
    highest_role: str


class TokenIdentity(BaseModel):
    sub: str
    email: str | None
    role: str
    is_superuser: bool = False
