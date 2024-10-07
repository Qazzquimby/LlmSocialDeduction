from aiohttp.web_response import BaseClass
from pydantic import BaseModel
from typing import Optional, List, Literal


class BaseEvent(BaseModel):
    type: str


from datetime import datetime
from pydantic import Field


class BaseMessage(BaseEvent):
    message: str
    username: str = "System"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    @property
    def ai_friendly_message(self):
        return self.message


class GameConnectMessage(BaseMessage):
    type: Literal["game_connect"] = "game_connect"
    gameId: str


class GameDisconnectMessage(BaseMessage):
    type: Literal["game_disconnect"] = "game_disconnect"


class GameStartedMessage(BaseMessage):
    type: Literal["game_started"] = "game_started"
    players: List[str]


class GameEndedMessage(BaseMessage):
    type: Literal["game_ended"] = "game_ended"


class PhaseMessage(BaseMessage):
    type: Literal["phase"] = "phase"
    phase: str


class SpeechMessage(BaseMessage):
    type: Literal["speech"] = "speech"

    @property
    def ai_friendly_message(self):
        return f"{self.username}: {self.message}"


class PromptChoice(BaseModel):
    index: int
    name: str


class PromptMessage(BaseMessage):
    type: Literal["prompt"] = "prompt"
    choices: Optional[List[PromptChoice]] = None
    multiple: bool = False
    min_choices: int = 1
    max_choices: Optional[int] = None

    @property
    def text(self):
        prompt_text = self.message
        if self.choices:
            prompt_text += "\nChoices:\n" + "\n".join(
                [f"{choice.index}: {choice.name}" for choice in self.choices]
            )
        if self.multiple:
            prompt_text += f"\nYou can select multiple choices (min: {self.min_choices}, max: {self.max_choices or 'unlimited'})."
        return prompt_text


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
