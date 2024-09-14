from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from games.one_night_ultimate_werewolf.game import OneNightWerewolf
import asyncio
from loguru import logger
from typing import Dict
import time

from message_types import GameConnectMessage, BaseMessage
from player import WebHumanPlayer


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(cleanup_inactive_games())
    yield


app = FastAPI(lifespan=lifespan)

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
last_activity: Dict[str, float] = {}
GAME_TIMEOUT = 3600  # 1 hour in seconds


async def cleanup_inactive_games():
    while True:
        current_time = time.time()
        for user_id, last_time in list(last_activity.items()):
            if current_time - last_time > GAME_TIMEOUT:
                logger.info(f"Cleaning up inactive game for user {user_id}")
                await end_game(user_id)
        await asyncio.sleep(60)  # Check every minute


async def end_game(user_id: str):
    if user_id in games:
        del games[user_id]
    if user_id in connections:
        await connections[user_id].send_json(
            {"type": "game_ended", "message": "Game ended due to inactivity"}
        )
        await connections[user_id].close()
        del connections[user_id]
    if user_id in last_activity:
        del last_activity[user_id]
    logger.info(f"Game ended for user {user_id}")


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
        result = await asyncio.wait_for(future, timeout)
        last_activity[user_id] = time.time()
        return result
    except asyncio.TimeoutError:
        del input_futures[user_id]
        raise TimeoutError(f"User {user_id} did not respond in time")
    finally:
        # Clean up the future if it's still there
        input_futures.pop(user_id, None)


async def notify_next_speaker(game_id: str, player_name: str):
    for user_id, game in games.items():
        if game.id == game_id:
            await connections[user_id].send_json(
                {"type": "next_speaker", "player": player_name}
            )
            last_activity[user_id] = time.time()


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    connections[user_id] = websocket
    last_activity[user_id] = time.time()

    logger.info(f"User {user_id} connected")

    if user_id not in games:
        game = OneNightWerewolf(num_players=5, has_human=True, user_id=user_id)
        games[user_id] = game
        await websocket.send_json(
            GameConnectMessage(
                message="Connection Established", gameId=game.id
            ).model_dump()
        )
        asyncio.create_task(game.play_game())
        logger.info(f"New game created for user {user_id}")
    else:
        # Resuming existing game
        game = games[user_id]
        game.websocket = websocket
        await websocket.send_json(
            GameConnectMessage(
                message="Reconnected to existing game", gameId=game.id
            ).model_dump()
        )
        web_human = [
            player for player in game.players if isinstance(player, WebHumanPlayer)
        ][0]
        logger.info(f"User {user_id} reconnected, catching up {web_human.name}")
        for observation in web_human.observations:
            await web_human.print(
                message=observation.message,
                observation_type=observation.observation_type,
                params=observation.params,
            )

    try:
        while True:
            data = await websocket.receive_json()
            last_activity[user_id] = time.time()
            logger.debug(f"Received data from user {user_id}: {data}")
            if user_id in input_futures:
                # Resolve the pending input future
                input_futures[user_id].set_result(data["message"])
            else:
                # Handle unexpected input
                logger.warning(f"Unexpected input from user {user_id}: {data}")
                await websocket.send_json(
                    BaseMessage(
                        type="error", message="No input was expected at this time."
                    ).model_dump()
                )
    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected")
    finally:
        connections.pop(user_id, None)
        logger.info(f"Connection closed for user {user_id}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
