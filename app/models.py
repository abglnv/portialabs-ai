from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class Service(BaseModel):
    ip: str = None
    domain: str = None
    token: str

class Report(BaseModel):
    exploit_id: str
    service_id: str
    user_id: str
    verdict: str
    description: str
    timestamp: datetime

class Technoly(BaseModel):
    name: str
    version: str
    description: str
    vendor: str
    service_id: str
    user_id: str
    timestamp: datetime