# Исследование производительности веб-сервисов на Python и Golang

## 1. Инициализируем локальный репозиторий

```aiignore
git init
```

Также создадим файл `.gitignore`, чтобы некоторые файлы не отслеживались и не загружались в удаленный репозиторий

```aiignore
.vscode
.venv
.env
.idea
__pycache__
.DS_Store
```

И создадим локальное окружение

```allignore
python -m venv .venv
source .venv/bin/activate
```

## 2. Создадим файл `.env` с переменными окружения

```aiignore
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=postgres
PG_DATABASE=postgres
```

Также продублируем эти данные в файл `.env.example`, который будет загружаться в удаленный репозиторий в отличие от оригинального файла `.env` и будет служить примером для заполнения оригинального файла

## 3. Поднимем Postgres с помощью Docker Compose

Предварительно необходимо установить [Docker Desktop](https://www.docker.com/products/docker-desktop/). Далее следует создать файл `docker-compose.yml`, в котором будет приведено описание образов, поднимаемых с помощью Docker Compose.

```yaml
services:
  pg:
    image: postgres:latest
    env_file:
      - .env
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=${PG_USER}
      - POSTGRES_PASSWORD=${PG_PASSWORD}
      - POSTGRES_DB=${PG_DATABASE}
    volumes:
      - ./init/pg/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: /usr/bin/pg_isready
      interval: 10s
      timeout: 10s
      retries: 5
```

Пропишем скрипт на SQL, который будет запускаться каждый раз при поднятии контейнера

```sql
// ./init/pg/init.sql

create extension if not exists "uuid-ossp";

create table if not exists person (
    id uuid default uuid_generate_v4(),
    name text not null,
    age int not null,
    address text not null,
    phone_number text not null,
    created_at timestamp default now(),
    updated_at timestamp default now(),
    deleted_at timestamp
);
```

Далее поднимаем Postgres с помощью Docker compose.

```bash
docker compose -f docker-compose.yml up -d -- build
```

## 4. Установим необходимые зависимости и настроим pre-commit

В том числе форматеры black, линтер flake8, пре-коммит хук pre-commit. Это позволит нам настроить автоматическую проверку кода перед каждым коммитом в репозиторий

```bash
pip install -r requirements.txt
```

Настроим пре-коммит, создав файл `.pre-commit-config.yaml` с соответствующим содержимым

```yaml
# .pre-commit-config.yaml

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-merge-conflict
      - id: trailing-whitespace
        args: [--markdown-linebreak-ext=md]
      - id: end-of-file-fixer
      - id: check-toml
      - id: check-yaml
        args: ["--unsafe"]
      - id: check-symlinks
      - id: check-added-large-files
        args: ["--maxkb=500"]
      - id: requirements-txt-fixer
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 24.2.0
    hooks:
      - id: black
        args:
          - --line-length=99
          - --exclude=/.venv/

  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args:
          - --max-line-length=99
```

Установим pre-commit

```bash
pip install pre-commit
pre-commit install
```

Вызывать пре-коммит можно следующим образом. Необходимо выполнять команду дважды: первый раз для форматирования и корректировки кода, второй раз для проверки

```bash
pre-commit run --all-files

# check for merge conflicts................................................Passed
# trim trailing whitespace.................................................Passed
# fix end of files.........................................................Passed
# check toml...........................................(no files to check)Skipped
# check yaml...............................................................Passed
# check for broken symlinks............................(no files to check)Skipped
# check for added large files..............................................Passed
# fix requirements.txt.....................................................Passed
# detect private key.......................................................Passed
# black....................................................................Passed
# flake8...................................................................Passed
# isort....................................................................Passed
```

## 5. Создание makefile для удобного управления нашим приложением

Но гораздо удобнее организовать вспомогательные команды с помощью `Makefile`

```make
.PHONY: up down

up:
	docker compose -f docker-compose.yaml up -d --build

down:
	docker compose -f docker-compose.yaml down -v
```

## 6. Создание веб-сервиса на Python

Содадим подпроект со следующей структурой

```bash
fastApiApp
├── Dockerfile
├── app
│   ├── db
│   │   └── postges.py
│   ├── handler
│   │   └── person.py
│   ├── main.py
│   ├── models
│   │   └── person.py
│   └── utils
│       └── utils.py
└── requirements.txt

6 directories, 7 files
```

Начнем с задания моделей данных

```python
# fastApiApp/app/models/person.py

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
```

Напишем функционал для работы с базой данных

```python
# fastApiApp/app/db/postgres.py

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
```

Напишем вспомогательный функционал

```python
# fastApiApp/app/utils/utils.py

from app.db.postges import session


def get_pg():
    db = session()
    try:
        yield db
    finally:
        db.close()
```

Напишем обработчики

```python
# fastApiApp/app/handler/person.py

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
```

Напишем точку входа в наш сервис

```python
# fastApi/app/main.py

import uvicorn
from fastapi import FastAPI
from app.handler.person import router as person_router

app = FastAPI()

app.include_router(person_router)


@app.get("/")
async def index():
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    uvicorn.run(app, port=8000)
```

Подготовим Dockerfile

```dockerfile
# fastApiApp/Dockerfile

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Не забудем приложить файл с зависимостями

```text
annotated-types==0.7.0
anyio==4.8.0
cfgv==3.4.0
click==8.1.8
distlib==0.3.9
Faker==35.2.0
fastapi==0.115.8
filelock==3.17.0
h11==0.14.0
identify==2.6.6
idna==3.10
nodeenv==1.9.1
platformdirs==4.3.6
pre_commit==4.1.0
psycopg2-binary==2.9.10
pydantic==2.10.6
pydantic_core==2.27.2
python-dateutil==2.9.0.post0
python-dotenv==1.0.1
PyYAML==6.0.2
six==1.17.0
sniffio==1.3.1
SQLAlchemy==2.0.37
starlette==0.45.3
typing_extensions==4.12.2
uvicorn==0.34.0
virtualenv==20.29.1
```

Теперь мы можем запустить наш сервис и базу данных

```bash
make up
```

## 7. Проводим нагрузочное тестирование веб-сервиса на Python с помощью [bombardier](https://github.com/codesenberg/bombardier)

```bash
bombardier -c 10 -n 1000 127.0.0.1:8000/person/ -m POST -H 'accept: application/json' -H 'Content-Type: application/json'

#Statistics        Avg      Stdev        Max
#Reqs/sec       586.46     150.86    1103.61
#Latency       17.09ms     6.39ms    59.32ms
#
#HTTP codes:
#1xx - 0, 2xx - 1000, 3xx - 0, 4xx - 0, 5xx - 0
#
#Throughput:   345.39KB/s

bombardier -c 10 -n 1000 127.0.0.1:8000/person/ -m GET -H 'accept: application/json' -H 'Content-Type: application/json'

#Statistics        Avg      Stdev        Max
#Reqs/sec        59.65      73.75     509.65
#Latency      167.52ms    38.58ms   370.89ms
#
#HTTP codes:
#1xx - 0, 2xx - 1000, 3xx - 0, 4xx - 0, 5xx - 0
#
#Throughput:    18.97MB/s
```
