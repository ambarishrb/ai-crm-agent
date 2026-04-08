from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import hcp, interaction, chat

app = FastAPI(title="HCP CRM API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hcp.router, prefix="/api")
app.include_router(interaction.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
