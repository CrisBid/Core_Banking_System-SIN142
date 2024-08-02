from fastapi import APIRouter, BackgroundTasks
from app.services import process_transacao

router = APIRouter()

@router.on_event("startup")
async def startup_event():
    process_transacao()

