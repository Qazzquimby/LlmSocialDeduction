from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from starlette.middleware.cors import CORSMiddleware
from games.one_night_ultimate_werewolf.game import OneNightWerewolf
import asyncio
from loguru import logger
from typing import Dict
import time

from message_types import GameConnectMessage, BaseMessage, PromptMessage, BaseEvent
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

    async def start(self):
        for websocket in self.connections.values():
            await websocket.send_json(
                GameConnectMessage(
                    message="Connection Established", gameId=self.game.id
                ).model_dump()
            )
        asyncio.create_task(self.game.play_game(), name=f"play_game, {self.game.id}")
        logger.info(f"New game created, {self.game.id}")

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

    async def receive_message(self, user_id: UserID):
        if user_id in self.message_queues:
            return await self.message_queues[user_id].get()

    def has_player(self, user_id: UserID):
        return user_id in [p.name for p in self.players]

    @property
    def players(self):
        return self.game.game_state.players

    async def end_game(self, user_id: UserID):
        if user_id in self.connections:
            await self.connections[user_id].send_json(
                {"type": "game_ended", "message": "Game ended due to inactivity"}
            )
            await self.connections[user_id].close()
            del self.connections[user_id]
        self.game_over = True
        logger.info(f"Game ended due to inactive {user_id}")

    # async def get_user_input(
    #     self, user_id: str, prompt_event: PromptMessage, timeout: float = 300
    # ) -> str:
    #     if user_id not in self.connections:
    #         raise ValueError(f"No active connection for user {user_id}")
    #
    #     # Create a future for this input request
    #     future = asyncio.Future()
    #     self.input_futures[user_id] = future
    #
    #     # Send the prompt to the user
    #     await self.connections[user_id].send_json(prompt_event.model_dump())
    #
    #     try:
    #         # Wait for the response with a timeout
    #         result = await asyncio.wait_for(future, timeout)
    #         self.last_activity[user_id] = time.time()
    #         return result
    #     except asyncio.TimeoutError:
    #         del self.input_futures[user_id]
    #         raise TimeoutError(f"User {user_id} did not respond in time")
    #     finally:
    #         # Clean up the future if it's still there
    #         await self.input_futures.pop(user_id, None)
    #
    # async def notify_next_speaker(self, player_name: str):
    #     for user_id in self.connections:
    #         await self.connections[user_id].send_json(
    #             {"type": "next_speaker", "player": player_name}
    #         )
    #         self.last_activity[user_id] = time.time()
    #
    # async def handle_input(self):
    #     while True:
    #         for user_id in self.connections.keys():
    #             await self.handle_input_for_player(user_id)
    #
    # async def handle_input_for_player(self, user_id: UserID):
    #     try:
    #         websocket = self.connections[user_id]
    #
    #         data = await websocket.receive_json()
    #         self.last_activity[user_id] = time.time()
    #         logger.debug(f"Received data from user {user_id}: {data}")
    #         if user_id in self.input_futures:
    #             # Resolve the pending input future
    #             self.input_futures[user_id].set_result(data["message"])
    #         else:
    #             # Handle unexpected input
    #             logger.warning(f"Unexpected input from user {user_id}: {data}")
    #             await websocket.send_json(
    #                 BaseMessage(
    #                     type="error", message="No input was expected at this time."
    #                 ).model_dump()
    #             )
    #
    #         # Log current game state
    #         logger.info(
    #             f"Current game state for user {user_id}: "
    #             f"Phase: {self.game.current_phase}, "
    #             f"Action: {self.game.current_action}"
    #         )
    #     except WebSocketDisconnect:
    #         logger.info(f"User {user_id} disconnected")
    #     except Exception as e:
    #         logger.error(f"An error occurred for user {user_id}: {str(e)}")
    #     finally:
    #         self.connections.pop(user_id, None)
    #         logger.info(f"Connection closed for user {user_id}")


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
        await game_manager.start()
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
    server_state: ServerState = Depends(get_server_state),
):
    logger.info(f"User {user_id} connected")

    found_game_with_player = False
    for game_manager in server_state.game_id_to_game_manager.values():
        if game_manager.has_player(user_id):
            await game_manager.resume_game(websocket=websocket, user_id=user_id)
            found_game_with_player = True
            break

    if not found_game_with_player:
        # no existing game found
        game_manager = await server_state.start_new_game(
            websocket=websocket, user_id=user_id
        )

    try:
        while True:
            data = await websocket.receive_json()
            await game_manager.message_queues[user_id].put(data)
    except WebSocketDisconnect:
        game_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Error in WebSocket handler for user {user_id}: {str(e)}")
        raise


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
