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
