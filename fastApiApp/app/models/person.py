import datetime
import uuid
from typing import List, Optional
from pydantic import BaseModel


class PersonResponse(BaseModel):
    id: uuid.UUID
    name: str
    age: int
    address: str
    phone_number: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    deleted_at: Optional[datetime.datetime] = None


class AllPersonResponse(BaseModel):
    persons: List[PersonResponse]
