from pydantic import BaseModel
from typing import Optional, List

class BaseMessage(BaseModel):
    type: str

class GameConnectMessage(BaseMessage):
    type: str = "game_connect"
    message: str
    gameId: str

class GameStartedMessage(BaseMessage):
    type: str = "game_started"
    players: List[str]

class PhaseMessage(BaseMessage):
    type: str = "phase"
    phase: str

class SpeechMessage(BaseMessage):
    type: str = "speech"
    username: str
    message: str

class PromptMessage(BaseMessage):
    type: str = "prompt"
    message: str

class NextSpeakerMessage(BaseMessage):
    type: str = "next_speaker"
    player: str

class PlayerActionMessage(BaseMessage):
    type: str = "player_action"
    player: str
    action: str
    message: Optional[str] = None
