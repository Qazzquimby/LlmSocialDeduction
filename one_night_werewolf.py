from typing import List

from ai_models import get_random_model
from model_performance import performance_tracker
from ai_personalities import PERSONALITIES
from player import Player, HumanPlayer, AIPlayer
from roles import assign_roles, get_roles_in_game
from game_state import GameState
from conversation import handle_conversations

class OneNightWerewolf:
    def __init__(self, num_players: int, has_human: bool = False):
        self.num_players: int = num_players
        self.has_human = has_human
        self.players: List[Player] = []
        self.game_state: GameState = GameState()

    def setup_game(self) -> None:
        # Create players
        if self.has_human:
            num_ai = self.num_players-1
            self.players.append(HumanPlayer(f"Human"))
        else:
            num_ai = self.num_players

        # AI_POOL = PERSONALITIES.copy()
        for i in range(num_ai):
            # name = random.choice(list(AI_POOL.keys()))
            # personality = AI_POOL[name]
            # del AI_POOL[name]

            model = get_random_model()
            name = f"{i}_{model}"

            player = AIPlayer(name=name, model=model)
            player.observations.append(f"Your name is {name}.")
            # player.observations.append(f"Your name is {name}. Personality: {personality}.")

            self.players.append(player)

        for player in self.players:
            player.observations.append(f"The players in this game are: {', '.join([p.name for p in self.players])}.")

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

        for player in self.players:
            print(f"{player.name} was a {player.role.name}.")

        return executed_players

    def check_win_condition(self, executed_players: List[Player]) -> None:
        werewolves = [p for p in self.players if p.role.name == "Werewolf"]
        village_wins = any(player in werewolves for player in executed_players) or not werewolves
        
        if village_wins:
            print("\nVillagers win!" + (" A Werewolf was executed." if werewolves else " There were no Werewolves in the game."))
        else:
            print("\nWerewolves win! No Werewolf was executed.")

        for player in self.players:
            if isinstance(player, AIPlayer):
                player_is_werewolf_team = player.role.name == "Werewolf"
                if player_is_werewolf_team:
                    player_won = not village_wins
                else:
                    player_won = village_wins

                performance_tracker.update_performance(player.model, player.total_cost, player_won)

        performance_tracker.save_performance_data()

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
    game = OneNightWerewolf(num_players=4, has_human=True)
    game.play_game()
