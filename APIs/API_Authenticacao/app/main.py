import asyncio
from fastapi import FastAPI
from app.consumers import consume_auth_requests

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, consume_auth_requests)
