from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from games.one_night_ultimate_werewolf.game import OneNightWerewolf
import asyncio
from loguru import logger
from typing import Dict

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
connections: Dict[str, WebSocket] = {}
games: Dict[str, OneNightWerewolf] = {}
input_futures: Dict[str, asyncio.Future] = {}


async def get_user_input(user_id: str, prompt: str, timeout: float = 300) -> str:
    if user_id not in connections:
        raise ValueError(f"No active connection for user {user_id}")

    # Create a future for this input request
    future = asyncio.Future()
    input_futures[user_id] = future

    # Send the prompt to the user
    await connections[user_id].send_json({"type": "prompt", "message": prompt})

    try:
        # Wait for the response with a timeout
        return await asyncio.wait_for(future, timeout)
    except asyncio.TimeoutError:
        del input_futures[user_id]
        raise TimeoutError(f"User {user_id} did not respond in time")
    finally:
        # Clean up the future if it's still there
        input_futures.pop(user_id, None)


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    connections[user_id] = websocket

    if user_id not in games:
        game = OneNightWerewolf(num_players=5, has_human=True, user_id=user_id)
        games[user_id] = game
        await websocket.send_json(
            {
                "type": "game_connect",
                "message": "Connection Established",
                "gameId": game.id,
            }
        )
        asyncio.create_task(game.play_game())
    else:
        # Resuming existing game
        game = games[user_id]
        game.websocket = websocket
        await websocket.send_json(
            {
                "type": "game_connect",
                "message": "Reconnected to existing game",
                "gameId": game.id,
            }
        )

    try:
        while True:
            data = await websocket.receive_json()
            if user_id in input_futures:
                # Resolve the pending input future
                input_futures[user_id].set_result(data["message"])
            else:
                # Handle unexpected input
                await websocket.send_json(
                    {"type": "error", "message": "No input was expected at this time."}
                )
    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected")
    finally:
        connections.pop(user_id, None)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
