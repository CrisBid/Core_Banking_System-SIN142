from fastapi import FastAPI
#from app.auth import jwt_handler
#from app import models, database

app = FastAPI()

#@app.on_event("startup")
#async def startup():
#    await database.connect()

#@app.on_event("shutdown")
#async def shutdown():
#    await database.disconnect()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI Auth Microservice"}

# Adicione suas rotas de autenticação e outras rotas aqui
