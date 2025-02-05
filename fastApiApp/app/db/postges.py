import uuid
import datetime
import os

import dotenv

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

dotenv.load_dotenv()

PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DATABASE = os.getenv("PG_DATABASE")

PG_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"

engine = sa.create_engine(PG_URL)

session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = sa.orm.declarative_base()


class PersonRecord(Base):
    __tablename__ = "person"

    id = sa.Column(sa.UUID, primary_key=True, index=True, default=uuid.uuid4)
    name = sa.Column(sa.String)
    age = sa.Column(sa.Integer)
    address = sa.Column(sa.String)
    phone_number = sa.Column(sa.String)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.now)
    updated_at = sa.Column(sa.DateTime, default=datetime.datetime.now)
    deleted_at = sa.Column(sa.DateTime, default=None)
