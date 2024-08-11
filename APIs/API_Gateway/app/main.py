from fastapi import FastAPI
from app.routes import router
from app.database import create_keyspace_and_table

app = FastAPI()
app.include_router(router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI Gateway Microservice"}

create_keyspace_and_table()

# Adicione suas rotas de autenticação e outras rotas aqui
