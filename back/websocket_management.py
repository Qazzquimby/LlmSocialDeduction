from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import asyncio

from loguru import logger
from pydantic import BaseModel
import hashlib

from message_types import BaseEvent, GameConnectMessage, PromptMessage


class UserLogin(BaseModel):
    name: str
    api_key: str

    @property
    def user_id(self) -> str:
        return hashlib.sha256(self.api_key.encode()).hexdigest()[:16]


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.input_queues: Dict[str, asyncio.Queue] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.message_queues[user_id] = asyncio.Queue()
        self.input_queues[user_id] = asyncio.Queue()

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)
        self.message_queues.pop(user_id, None)
        self.input_queues.pop(user_id, None)

    async def send_personal_message(self, message: BaseEvent, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message.model_dump())
            except RuntimeError as e:
                raise RuntimeError(f"User {user_id} unexpectedly disconnected", e)
        else:
            raise RuntimeError(f"User {user_id} not connected")

    async def broadcast(self, message: BaseEvent, users: List[str]):
        for user_id in users:
            await self.send_personal_message(message, user_id)

    async def receive_message(self, user_id: str):
        if user_id in self.message_queues:
            return await self.message_queues[user_id].get()

    async def get_input(self, user_id: str, prompt: PromptMessage):
        await self.send_personal_message(prompt, user_id)
        return await self.input_queues[user_id].get()

    async def listen_on_connection(self, websocket: WebSocket, user_id: str):
        logger.info(f"listening to {user_id}")
        try:
            while True:
                data = await websocket.receive_json()
                if isinstance(data, dict) and data.get("type") == "input":
                    await self.input_queues[user_id].put(data["message"])
                else:
                    await self.message_queues[user_id].put(data)
        except WebSocketDisconnect:
            self.disconnect(user_id)
        finally:
            logger.info(f"done listening to {user_id}")

    async def resume_game(self, user_id: str, game_id: str, web_human_player):
        await self.send_personal_message(
            GameConnectMessage(message="Reconnected to existing game", gameId=game_id),
            user_id,
        )

        if web_human_player:
            for observation in web_human_player.observations:
                await self.send_personal_message(observation, user_id)


websocket_manager = WebSocketManager()
