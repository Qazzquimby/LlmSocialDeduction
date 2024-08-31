import random
from player import Player
from roles import assign_roles
from game_state import GameState
from conversation import handle_conversations

class OneNightWerewolf:
    def __init__(self, num_players, num_random_ai):
        self.num_players = num_players
        self.num_random_ai = num_random_ai
        self.players = []
        self.game_state = GameState()

    def setup_game(self):
        # Create players
        for i in range(self.num_players):
            if i < self.num_random_ai:
                self.players.append(Player(f"Random AI {i+1}", agent_type='random'))
            else:
                self.players.append(Player(f"Human Player {i+1-self.num_random_ai}", agent_type='human'))

        # Assign roles
        center_cards = assign_roles(self.players)
        self.game_state.add_center_cards(center_cards)

    def play_night_phase(self):
        print("\n--- Night Phase ---")
        for player in self.players:
            action = player.night_action(self.game_state)
            if action:
                self.game_state.record_night_action(player, action)

    def play_day_phase(self):
        print("\n--- Day Phase ---")
        handle_conversations(self.players)

    def voting_phase(self):
        print("\n--- Voting Phase ---")
        votes = {}
        for player in self.players:
            voted_player = player.vote([p for p in self.players if p != player])
            votes[player] = voted_player
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

    def check_win_condition(self, executed_players):
        werewolves = [p for p in self.players if p.role.name == "Werewolf"]
        
        if any(player in werewolves for player in executed_players):
            print("\nVillagers win! A Werewolf was executed.")
        elif not werewolves:
            print("\nVillagers win! There were no Werewolves in the game.")
        else:
            print("\nWerewolves win! No Werewolf was executed.")

    def play_game(self):
        self.setup_game()
        self.play_night_phase()
        self.play_day_phase()
        executed_players = self.voting_phase()
        self.check_win_condition(executed_players)

if __name__ == "__main__":
    game = OneNightWerewolf(num_players=6, num_random_ai=3)
    game.play_game()
