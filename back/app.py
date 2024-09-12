from fastapi import FastAPI, WebSocket
from starlette.middleware.cors import CORSMiddleware
from games.one_night_ultimate_werewolf.game import OneNightWerewolf
import asyncio
from loguru import logger

app = FastAPI()

# Configure loguru
logger.add("app.log", rotation="500 MB", level="DEBUG")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Store active connections and games
active_connections = {}
games = {}



@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    if username not in active_connections:
        active_connections[username] = websocket

    # Send connection confirmation
    await websocket.send_json({"type": "engine", "message": "Connection Established"})

    game = OneNightWerewolf(num_players=5, has_human=True, websocket=websocket)
    await game.play_game()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
