from pydantic import BaseModel
from typing import Optional, List


class BaseEvent(BaseModel):
    type: str


class BaseMessage(BaseEvent):
    message: str


class GameConnectMessage(BaseMessage):
    type: str = "game_connect"
    gameId: str


class GameStartedMessage(BaseEvent):
    type: str = "game_started"
    players: List[str]


class PhaseMessage(BaseEvent):
    type: str = "phase"
    phase: str


class SpeechMessage(BaseMessage):
    type: str = "speech"
    username: str


class PromptMessage(BaseMessage):
    type: str = "prompt"


class NextSpeakerMessage(BaseEvent):
    type: str = "next_speaker"
    player: str


class PlayerActionMessage(BaseMessage):
    type: str = "player_action"
    player: str
    action: str
    message: Optional[str] = None
