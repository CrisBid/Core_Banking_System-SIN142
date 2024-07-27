from fastapi import APIRouter
from app.services import process_authentication

router = APIRouter()

@router.on_event("startup")
async def startup_event():
    process_authentication()

