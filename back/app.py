from fastapi import FastAPI, WebSocket, Depends, BackgroundTasks
from starlette.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect

from games.one_night_ultimate_werewolf.game import OneNightWerewolf
import asyncio
from loguru import logger
from typing import Dict

from message_types import (
    BaseMessage,
    GameEndedMessage,
    PromptMessage,
)
from player import WebHumanPlayer
from websocket_management import websocket_manager, UserLogin

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

    def remove_player(self, user_id: UserID):
        player = self.get_web_human_player(user_id)
        if player:
            self.game.state.players.remove(player)
            logger.info(f"Removed player {user_id} from game {self.game.id}")

    async def end_game(self):
        for player in self.web_players:
            await websocket_manager.send_personal_message(
                BaseMessage(type="game_ended", message="Game ended due to inactivity"),
                player.user_id,
            )
        self.game.game_over = True
        logger.info("Game ended due to inactivity")


class ServerState:
    def __init__(self):
        self.game_id_to_game_manager: Dict[GameID, GameManager] = {}

    async def setup_new_game(self, login: UserLogin):
        game = OneNightWerewolf(num_players=5, has_human=True, login=login)
        game_manager = GameManager(game)
        self.game_id_to_game_manager[game.id] = game_manager
        return game_manager


_server_state = ServerState()


def get_server_state():
    return _server_state


@app.get("/debug")
async def debug():
    for task in asyncio.all_tasks():
        name = task.get_name()
        qual_name = task.get_coro().__qualname__
        logger.info(f"Task {name}: {qual_name}")
        if task.done():
            if task.exception():
                logger.error(f"Task {name} failed with exception: {task.exception()}")
            else:
                logger.info(f"Task {name} completed successfully")
    print("DEBUG")
    return


@app.websocket("/ws/{name}")
async def websocket_endpoint(
    websocket: WebSocket,
    name: str,
    api_key: str = None,
    server_state: ServerState = Depends(get_server_state),
):
    user_login = UserLogin(name=name, api_key=api_key)
    user_id = user_login.user_id
    logger.info(f"User {name} (ID: {user_id}) connected")

    await websocket_manager.connect(websocket, user_id)

    found_game_with_player = False
    for game_id, game_manager in list(server_state.game_id_to_game_manager.items()):
        if game_manager.has_player(user_id):
            if game_manager.game.game_over:
                # Remove the game that's no longer running
                del server_state.game_id_to_game_manager[game_id]
                await websocket_manager.send_personal_message(
                    GameEndedMessage(
                        message="The game you were in has ended. You can start a new game."
                    ),
                    user_id,
                )
            else:
                web_human_player = game_manager.get_web_human_player(user_id)
                await websocket_manager.resume_game(
                    user_id, game_manager.game.id, web_human_player
                )
                # Resend the last prompt message if it exists
                last_prompt = next(
                    (
                        msg
                        for msg in reversed(web_human_player.observations)
                        if isinstance(msg, PromptMessage)
                    ),
                    None,
                )
                if last_prompt:
                    await websocket_manager.send_personal_message(last_prompt, user_id)
                found_game_with_player = True
            break

    if not found_game_with_player:
        # If the game is not found or has ended, disconnect the user from their game ID
        await websocket_manager.send_personal_message(
            GameEndedMessage(message="No active game"),
            user_id,
        )

    try:
        await websocket_manager.listen_on_connection(websocket, user_id, server_state)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
        await websocket_manager.disconnect(user_id)


@app.post("/start_game")
async def start_game(
    user_login: UserLogin,
    background_tasks: BackgroundTasks,
    server_state: ServerState = Depends(get_server_state),
):
    game_manager = await server_state.setup_new_game(login=user_login)

    background_tasks.add_task(game_manager.game.play_game)
    # asyncio.create_task(
    #     game_manager.game.play_game(),
    #     name=f"play_game, {game_manager.game.id}",
    # )

    return {"gameId": game_manager.game.id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
