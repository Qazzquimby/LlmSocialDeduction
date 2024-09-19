from pydantic import BaseModel


class UserLogin(BaseModel):
    name: str
    api_key: str
