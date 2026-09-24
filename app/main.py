import os

from fastapi import FastAPI
from routes.extracao import extraction_router

app = FastAPI(root_path=os.getenv("FROTA_ROOT_PATH", ""))

app.include_router(extraction_router)
