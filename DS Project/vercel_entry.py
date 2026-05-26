# vercel_entry.py
"""Vercel entry point for FastAPI.
This file resides in a space‑free location so Vercel can import it.
It mirrors the logic from `api/app.py` but sets the static directory
relative to this file's location.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

# Import helper functions from the existing module
from predictor import load_from_csv, predict_player

app = FastAPI()

# Frontend directory is a sibling of this file
STATIC_DIR = Path(__file__).parent / "frontend"

# Serve static assets (CSS, JS) under /static
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=FileResponse)
def root():
    """Serve the main HTML page."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not built")
    return FileResponse(index_path)

@app.get("/players")
def get_players():
    """Return the full list of player records as JSON."""
    try:
        return load_from_csv()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/forecast/{player_id}")
def get_forecast(player_id: int, games_left: int = 8):
    """Return forecast data for a specific player.

    The `player_id` field must exist in the CSV. If it does not, a 404 is raised.
    """
    all_players = load_from_csv()
    player = next((p for p in all_players if p.get("player_id") == player_id), None)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    forecasts = predict_player(player, all_players, games_left=games_left)
    if not forecasts:
        raise HTTPException(status_code=400, detail="Insufficient data for forecast")
    return forecasts
