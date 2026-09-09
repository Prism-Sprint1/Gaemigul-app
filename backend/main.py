from fastapi import FastAPI
from src.backend.domain.calendar.routers.calendar import router as calendar_router

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "hello world입니다."}


app.include_router(calendar_router)