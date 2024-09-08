from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING, List

if TYPE_CHECKING:
    from game_state import GameState
    from player import Player

@dataclass
class RoleInteraction:
    other_role: "Role"
    interaction: str


class Role:
    def __init__(self, name: str):
        self.name: str = name

    def night_action(self, player: 'Player', game_state: 'GameState') -> Optional[str]:
        return None

    def get_rules(self) -> str:
        raise NotImplementedError

    def get_strategy(self, game_state: 'GameState') -> str:
        strategy = "\n".join(self.get_general_strategy_lines())

        interaction_lines = []
        for line in self.get_interaction_strategy_lines():
            if line.other_role in game_state.role_pool:
                interaction_lines.append(line.interaction)
        strategy += "\n".join(interaction_lines)

        return strategy

    def get_general_strategy_lines(self) -> List[str]:
        raise NotImplementedError

    def get_interaction_strategy_lines(self)-> List[RoleInteraction]:
        return []

    def did_win(self, player: 'Player', executed_players: List['Player'], werewolves_exist: bool) -> bool:
        raise NotImplementedError

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name