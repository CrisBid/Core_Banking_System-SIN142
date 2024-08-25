from fastapi import APIRouter, BackgroundTasks
from app.consumer import start_consumer

router = APIRouter()

@router.on_event("startup")
async def startup_event():
    start_consumer()