from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers.xp_operations import router as xp_operations_router
from .routers.drawing_games import router as drawing_games_router
from .routers import (
    admin,
    attendance,
    auth,
    challenges,
    gamification,
    leaderboard,
    player,
    public,
    recognition,
    reward_games,
)

app = FastAPI(
    title="Digital Youth Platform",
    version="2.0.0",
)

app.include_router(xp_operations_router)
app.include_router(drawing_games_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(player.router)
app.include_router(leaderboard.router)
app.include_router(attendance.router)
app.include_router(admin.router)
app.include_router(public.router)
app.include_router(gamification.router)
app.include_router(challenges.router)
app.include_router(recognition.router)
app.include_router(reward_games.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


frontend = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "dist"
)

if frontend.exists():
    app.mount(
        "/",
        StaticFiles(
            directory=frontend,
            html=True,
        ),
        name="frontend",
    )