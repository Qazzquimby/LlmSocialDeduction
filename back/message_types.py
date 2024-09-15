from pydantic import BaseModel
from typing import Optional, List, Literal


class BaseEvent(BaseModel):
    type: str


class BaseMessage(BaseEvent):
    message: str
    username: str = "System"


class GameConnectMessage(BaseMessage):
    type: Literal["game_connect"] = "game_connect"
    gameId: str


class GameStartedMessage(BaseMessage):
    type: Literal["game_started"] = "game_started"
    players: List[str]


class PhaseMessage(BaseMessage):
    type: Literal["phase"] = "phase"
    phase: str


class SpeechMessage(BaseMessage):
    type: Literal["speech"] = "speech"


class PromptMessage(BaseMessage):
    type: Literal["prompt"] = "prompt"


class NextSpeakerMessage(BaseEvent):
    type: Literal["next_speaker"] = "next_speaker"
    player: str


class PlayerActionMessage(BaseMessage):
    type: Literal["player_action"] = "player_action"
    player: str
    action: str
    message: Optional[str] = None


class ObservationMessage(BaseMessage):
    type: Literal["observation"] = "observation"


class RulesError(BaseMessage):
    type: Literal["rules_error"] = "rules_error"
