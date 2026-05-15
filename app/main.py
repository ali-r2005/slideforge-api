from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1.endpoints import router

from pathlib import Path

app = FastAPI()

# Ensure required directories exist
Path("public/thumbnails").mkdir(parents=True, exist_ok=True)
Path("generated").mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/generated", StaticFiles(directory="generated"), name="generated")
app.mount("/thumbnails", StaticFiles(directory="public/thumbnails"), name="thumbnails")



app.include_router(router)
