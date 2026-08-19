from fastapi import FastAPI
from routes.extracao import extraction_router

app = FastAPI()

app.include_router(extraction_router)

