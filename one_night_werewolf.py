from typing import List
from player import Player, HumanPlayer, AIPlayer
from roles import assign_roles, get_roles_in_game
from game_state import GameState
from conversation import handle_conversations

class OneNightWerewolf:
    def __init__(self, num_players: int, num_ai: int=None):
        self.num_players: int = num_players

        if num_ai is None:
            num_ai = num_players

        self.num_ai: int = num_ai
        self.players: List[Player] = []
        self.game_state: GameState = GameState()

    def setup_game(self) -> None:
        # Create players
        for i in range(self.num_players):
            if i < self.num_ai:
                self.players.append(AIPlayer(f"AI{i}"))
            else:
                self.players.append(HumanPlayer(f"Human{i}"))

        # Assign roles
        roles_in_game = get_roles_in_game(len(self.players))
        center_cards = assign_roles(self.players, roles_in_game=roles_in_game)
        for player in self.players:
            player.observations.append(f"The full role pool in this game are: {', '.join([role.name for role in roles_in_game])}. Remember that 3 of them are in the center, not owned by other players.")
        self.game_state.add_center_cards(center_cards)
        self.game_state.set_players(self.players)

    def think(self):
        for player in self.players:
            player.think()

    def play_night_phase(self) -> None:
        print("\n--- Night Phase ---")
        role_order = ["Werewolf", "Seer", "Robber", "Troublemaker"]
        for role in role_order:
            for player in self.players:
                if player.original_role.name == role:
                    action = player.night_action(self.game_state)
                    if action:
                        self.game_state.record_night_action(player, action)

    def play_day_phase(self) -> None:
        print("\n--- Day Phase ---")
        handle_conversations(self.players)

    def voting_phase(self) -> List[Player]:
        print("\n--- Voting Phase ---")

        votes = {}
        for player in self.players:
            voted_player = player.vote([p for p in self.players if p != player])
            votes[player] = voted_player

        print("Votes:")
        for player, voted_player in votes.items():
            print(f"{player.name} voted for {voted_player.name}")

        # Count votes
        vote_count = {}
        for voted_player in votes.values():
            vote_count[voted_player] = vote_count.get(voted_player, 0) + 1

        # Find player(s) with the most votes
        max_votes = max(vote_count.values())
        executed_players = [p for p, v in vote_count.items() if v == max_votes]

        if len(executed_players) == 1:
            print(f"\n{executed_players[0].name} has been executed!")
        else:
            print("\nIt's a tie! No one has been executed.")

        return executed_players

    def check_win_condition(self, executed_players: List[Player]) -> None:
        werewolves = [p for p in self.players if p.role.name == "Werewolf"]
        
        if any(player in werewolves for player in executed_players):
            print("\nVillagers win! A Werewolf was executed.")
        elif not werewolves:
            print("\nVillagers win! There were no Werewolves in the game.")
        else:
            print("\nWerewolves win! No Werewolf was executed.")

    def play_game(self) -> None:
        self.setup_game()
        self.think()

        self.play_night_phase()
        self.think()

        self.play_day_phase()
        self.think()

        executed_players = self.voting_phase()
        self.check_win_condition(executed_players)

if __name__ == "__main__":
    game = OneNightWerewolf(num_players=4, num_ai=2)
    game.play_game()
