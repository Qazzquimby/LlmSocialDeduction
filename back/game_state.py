from typing import List, Tuple, TYPE_CHECKING
from games.one_night_ultimate_werewolf.onuw_roles import Role

if TYPE_CHECKING:
    from .player import Player

class GameState:
    def __init__(self, num_players: int):
        self.center_cards: List[Role] = []
        self.night_actions: List[Tuple['Player', str]] = []
        self.day_actions: List[Tuple['Player', str]] = []
        self.players: List['Player'] = []
        self.role_pool: List[Role] = []
        self.num_players = num_players

    def add_center_cards(self, cards: List[Role]) -> None:
        self.center_cards = cards

    def add_player(self, player: 'Player') -> None:
        if len(self.players) < self.num_players:
            self.players.append(player)
        else:
            raise ValueError("Maximum number of players reached")

    def record_night_action(self, player: 'Player', action: str) -> None:
        self.night_actions.append((player, action))

    def record_day_action(self, player: 'Player', action: str) -> None:
        self.day_actions.append((player, action))

    def get_player_role(self, player: 'Player') -> Role:
        # This method might be used to get a player's current role,
        # considering any role switches that happened during the night
        return player.role
