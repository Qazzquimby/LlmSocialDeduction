import json
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

    while True:
        data = await websocket.receive_text()
        message = json.loads(data)

        logger.debug(f"Received message from {username}: {message}")

        if message['type'] == 'new_game':
            game = OneNightWerewolf(num_players=message['num_players'], has_human=True,
                                    websocket=websocket)
            games[username] = game
            await asyncio.create_task(game.play_game())

        elif message['type'] == 'player_action':
            # Handle player actions (night actions, speaking, voting)
            game = games[username]
            player = next(p for p in game.players if p.name == message['player'])
            result = await player.handle_action(message['action'], game.game_state)
            await websocket.send_json(
                {'type': 'action_result', 'player': player.name, 'result': result})

        else:
            await websocket.send_json(message)


async def broadcast(username: str, message: dict):
    if username in active_connections:
        await active_connections[username].send_text(json.dumps(message))


# Add a new route for testing
@app.get("/test")
async def endpoint_test():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
