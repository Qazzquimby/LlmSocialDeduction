from typing import List, Tuple, TYPE_CHECKING
from games.one_night_ultimate_werewolf.roles import Role

if TYPE_CHECKING:
    from .player import Player

class GameState:
    def __init__(self):
        self.center_cards: List[Role] = []
        self.night_actions: List[Tuple['Player', str]] = []
        self.day_actions: List[Tuple['Player', str]] = []
        self.players: List['Player'] = []
        self.role_pool: List[Role] = []

    def add_center_cards(self, cards: List[Role]) -> None:
        self.center_cards = cards

    def set_players(self, players: List['Player']) -> None:
        self.players = players

    def record_night_action(self, player: 'Player', action: str) -> None:
        self.night_actions.append((player, action))

    def record_day_action(self, player: 'Player', action: str) -> None:
        self.day_actions.append((player, action))

    def get_player_role(self, player: 'Player') -> Role:
        # This method might be used to get a player's current role,
        # considering any role switches that happened during the night
        return player.role
