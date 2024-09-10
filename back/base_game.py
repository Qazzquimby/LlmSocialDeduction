from typing import List
from player import Player
from game_state import GameState

class Game:
    def __init__(self, num_players: int, has_human: bool = False):
        self.num_players: int = num_players
        self.has_human: bool = has_human
        self.players: List[Player] = []
        self.game_state: GameState = GameState()

    def setup_game(self) -> None:
        raise NotImplementedError("Subclasses must implement setup_game method")

    def play_game(self) -> None:
        raise NotImplementedError("Subclasses must implement play_game method")

    def think(self) -> None:
        for player in self.players:
            player.think()

    def check_win_condition(self, executed_players: List[Player]) -> None:
        raise NotImplementedError("Subclasses must implement check_win_condition method")
