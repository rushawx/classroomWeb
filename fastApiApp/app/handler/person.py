from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from faker import Faker
import uuid

from app.db.postges import PersonRecord
from app.models.person import PersonResponse, AllPersonResponse
from app.utils.utils import get_pg

router = APIRouter(
    prefix="/person",
    tags=["person"],
)

faker = Faker("ru_RU")


@router.post("/")
def post_record(db: Session = Depends(get_pg)) -> PersonResponse:
    record = PersonRecord(
        id=uuid.uuid4(),
        name=faker.name(),
        age=faker.random_int(min=18, max=99),
        address=faker.address(),
        phone_number=faker.phone_number(),
        created_at=faker.date_time_between(start_date="-1y", end_date="now"),
        updated_at=faker.date_time_between(start_date="-1y", end_date="now"),
        deleted_at=None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return PersonResponse(
        id=record.id,
        name=record.name,
        age=record.age,
        address=record.address,
        phone_number=record.phone_number,
        created_at=record.created_at,
        updated_at=record.updated_at,
        deleted_at=None,
    )


@router.get("/")
async def get_records(db: Session = Depends(get_pg)) -> AllPersonResponse:
    records = db.query(PersonRecord).all()
    output = []
    for record in records:
        output.append(
            PersonResponse(
                id=record.id,
                name=record.name,
                age=record.age,
                address=record.address,
                phone_number=record.phone_number,
                created_at=record.created_at,
                updated_at=record.updated_at,
                deleted_at=None,
            )
        )
    return AllPersonResponse(persons=output)
