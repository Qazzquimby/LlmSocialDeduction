from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from starlette.middleware.cors import CORSMiddleware
from games.one_night_ultimate_werewolf.game import OneNightWerewolf
import asyncio
from loguru import logger
from typing import Dict
import time

from message_types import GameConnectMessage, BaseEvent
from player import WebHumanPlayer

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

        self.connections: Dict[UserID, WebSocket] = {}
        self.input_futures: Dict[UserID, asyncio.Future] = {}
        self.last_activity: Dict[UserID, float] = {}
        self.message_queues: Dict[UserID, asyncio.Queue] = {}

    async def resume_game(self, websocket: WebSocket, user_id: UserID):
        await self.connect_player(user_id=user_id, websocket=websocket)
        await websocket.send_json(
            GameConnectMessage(
                message="Reconnected to existing game", gameId=self.game.id
            ).model_dump()
        )

        web_human = [
            player for player in self.game.players if isinstance(player, WebHumanPlayer)
        ][0]
        logger.info(f"User {user_id} reconnected, catching up {user_id}")
        for observation in web_human.observations:
            await web_human.print(observation)

    async def connect_player(self, user_id: UserID, websocket: WebSocket):
        await websocket.accept()
        self.connections[user_id] = websocket
        self.message_queues[user_id] = asyncio.Queue()

    def disconnect(self, user_id: UserID):
        self.connections.pop(user_id, None)
        self.message_queues.pop(user_id, None)

    async def send_message(self, user_id: UserID, message: BaseEvent):
        connection = self.connections[user_id]
        await connection.send_json(message.model_dump())

    async def get_input(self, user_id: UserID, message: BaseEvent):
        await self.send_message(user_id=user_id, message=message)
        message = await self._receive_message(user_id)
        return message

    async def _receive_message(self, user_id: UserID):
        if user_id in self.message_queues:
            message_dict = await self.message_queues[user_id].get()
            message = message_dict["message"]
            return message

    def has_player(self, user_id: UserID):
        return user_id in [p.user_id for p in self.web_players]

    @property
    def players(self):
        return self.game.game_state.players

    @property
    def web_players(self):
        return [p for p in self.players if isinstance(p, WebHumanPlayer)]

    async def end_game(self, user_id: UserID):
        if user_id in self.connections:
            await self.connections[user_id].send_json(
                {"type": "game_ended", "message": "Game ended due to inactivity"}
            )
            await self.connections[user_id].close()
            del self.connections[user_id]
        self.game_over = True
        logger.info(f"Game ended due to inactive {user_id}")

    async def notify_next_speaker(self, player_name: str):
        for user_id in self.connections:
            await self.connections[user_id].send_json(
                {"type": "next_speaker", "player": player_name}
            )
            self.last_activity[user_id] = time.time()


class ServerState:
    def __init__(self):
        self.game_id_to_game_manager: Dict[GameID, GameManager] = {}

    async def start_new_game(self, websocket: WebSocket, user_id: UserID):
        game_manager = GameManager(
            OneNightWerewolf(num_players=5, has_human=True, user_id=user_id)
        )
        game_manager.game.game_manager = game_manager  # gross

        await game_manager.connect_player(user_id=user_id, websocket=websocket)

        self.game_id_to_game_manager[game_manager.game.id] = game_manager
        return game_manager


_server_state = ServerState()


def get_server_state():
    return _server_state


async def listen_for_player_input(game_manager: GameManager, websocket, user_id):
    try:
        while True:
            data = await websocket.receive_json()
            await game_manager.message_queues[user_id].put(data)
    except WebSocketDisconnect:
        game_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Error in WebSocket handler for user {user_id}: {str(e)}")
        raise


@app.get("/debug")
async def debug():
    print("DEBUG")
    return


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: UserID,
    server_state: ServerState = Depends(get_server_state),
):
    logger.info(f"User {user_id} connected")

    found_game_with_player = False
    for game_manager in server_state.game_id_to_game_manager.values():
        if game_manager.has_player(user_id):
            await game_manager.resume_game(websocket=websocket, user_id=user_id)
            found_game_with_player = True

            await listen_for_player_input(
                game_manager=game_manager, websocket=websocket, user_id=user_id
            )
            return

    if not found_game_with_player:
        # no existing game found
        game_manager = await server_state.start_new_game(
            websocket=websocket, user_id=user_id
        )
        listen_task = listen_for_player_input(
            game_manager=game_manager, websocket=websocket, user_id=user_id
        )
        run_game_task = asyncio.create_task(
            game_manager.game.play_game(), name=f"play_game, {game_manager.game.id}"
        )
        await asyncio.gather(listen_task, run_game_task)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
