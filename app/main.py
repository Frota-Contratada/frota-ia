from fastapi import FastAPI
from routes.extracao import extraction_router
from routes.leitura import leitor_router
from app.config import Settings

app = FastAPI()

app.include_router(extraction_router)
app.include_router(leitor_router)
