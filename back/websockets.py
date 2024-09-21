from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import asyncio

from pydantic import BaseModel

from message_types import BaseEvent, GameConnectMessage


class UserLogin(BaseModel):
    name: str
    api_key: str


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.message_queues: Dict[str, asyncio.Queue] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.message_queues[user_id] = asyncio.Queue()

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)
        self.message_queues.pop(user_id, None)

    async def send_personal_message(self, message: BaseEvent, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message.model_dump())

    async def broadcast(self, message: BaseEvent, users: List[str]):
        for user_id in users:
            await self.send_personal_message(message, user_id)

    async def receive_message(self, user_id: str):
        if user_id in self.message_queues:
            return await self.message_queues[user_id].get()

    async def handle_connection(self, websocket: WebSocket, user_id: str, game_manager):
        await self.connect(websocket, user_id)
        try:
            while True:
                data = await websocket.receive_json()
                await self.message_queues[user_id].put(data)
        except WebSocketDisconnect:
            self.disconnect(user_id)
            game_manager.disconnect(user_id)

    async def resume_game(self, user_id: str, game_id: str, game_manager):
        await self.send_personal_message(
            GameConnectMessage(message="Reconnected to existing game", gameId=game_id),
            user_id,
        )

        web_human = game_manager.get_web_human_player(user_id)
        if web_human:
            for observation in web_human.observations:
                await self.send_personal_message(observation, user_id)


websocket_manager = WebSocketManager()
