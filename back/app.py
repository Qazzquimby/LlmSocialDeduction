from fastapi import FastAPI, WebSocket, Depends
from starlette.middleware.cors import CORSMiddleware
from games.one_night_ultimate_werewolf.game import OneNightWerewolf
import asyncio
from loguru import logger
from typing import Dict
import time

from message_types import BaseEvent
from player import WebHumanPlayer
from websocket_login import UserLogin
from websocket_manager import websocket_manager

app = FastAPI(debug=True)

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

GameID = str
UserID = str


class GameManager:
    GAME_TIMEOUT = 3600  # 1 hour in seconds

    def __init__(self, game: OneNightWerewolf):
        self.game: OneNightWerewolf = game
        self.game_over = False
        self.last_activity: Dict[UserID, float] = {}

    def disconnect(self, user_id: UserID):
        self.last_activity.pop(user_id, None)

    def has_player(self, user_id: UserID):
        return user_id in [p.user_id for p in self.web_players]

    @property
    def players(self):
        return self.game.state.players

    @property
    def web_players(self):
        return [p for p in self.players if isinstance(p, WebHumanPlayer)]

    def get_web_human_player(self, user_id: UserID):
        return next((p for p in self.web_players if p.user_id == user_id), None)

    async def end_game(self, user_id: UserID):
        await websocket_manager.send_personal_message(
            BaseEvent(type="game_ended", message="Game ended due to inactivity"),
            user_id,
        )
        self.game_over = True
        logger.info(f"Game ended due to inactive {user_id}")

    async def notify_next_speaker(self, player_name: str):
        await websocket_manager.broadcast(
            BaseEvent(type="next_speaker", player=player_name),
            [p.user_id for p in self.web_players],
        )
        for user_id in self.web_players:
            self.last_activity[user_id.user_id] = time.time()


class ServerState:
    def __init__(self):
        self.game_id_to_game_manager: Dict[GameID, GameManager] = {}

    async def start_new_game(self, login: UserLogin):
        game_manager = GameManager(
            OneNightWerewolf(num_players=5, has_human=True, login=login)
        )
        game_manager.game.game_manager = game_manager  # todo, gross.

        self.game_id_to_game_manager[game_manager.game.id] = game_manager
        return game_manager


_server_state = ServerState()


def get_server_state():
    return _server_state


@app.get("/debug")
async def debug():
    print("DEBUG")
    return


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: UserID,
    api_key: str = None,
    server_state: ServerState = Depends(get_server_state),
):
    logger.info(f"User {user_id} connected")

    found_game_with_player = False
    for game_manager in server_state.game_id_to_game_manager.values():
        if game_manager.has_player(user_id):
            await websocket_manager.resume_game(
                user_id, game_manager.game.id, game_manager
            )
            found_game_with_player = True
            break

    if not found_game_with_player:
        game_manager = await server_state.start_new_game(
            login=UserLogin(name=user_id, api_key=api_key)
        )

    await websocket_manager.handle_connection(websocket, user_id, game_manager)

    if not found_game_with_player:
        run_game_task = asyncio.create_task(
            game_manager.game.play_game(),
            name=f"play_game, {game_manager.game.id}",
        )
        await run_game_task


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
