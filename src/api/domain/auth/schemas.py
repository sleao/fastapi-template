from pydantic import BaseModel


class UserIdentity(BaseModel):
    id: int
    company_id: int
    role: str | None = None
