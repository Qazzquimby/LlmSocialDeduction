import random
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from game_state import GameState
    from player import Player

class Role:
    def __init__(self, name: str):
        self.name: str = name

    def night_action(self, player: 'Player', game_state: 'GameState') -> Optional[str]:
        return None

class Werewolf(Role):
    def __init__(self):
        super().__init__("Werewolf")

    def night_action(self, player: "Player", game_state: "GameState") -> str:
        other_werewolves = [p for p in game_state.players if p != player and isinstance(p.role, Werewolf)]
        other_werewolves_names = ", ".join(w.name for w in other_werewolves) if other_werewolves else "no one"
        return f"You see that {other_werewolves_names} is/are also Werewolf/Werewolves."

class Villager(Role):
    def __init__(self):
        super().__init__("Villager")

class Seer(Role):
    def __init__(self):
        super().__init__("Seer")

    def night_action(self, player: "Player", game_state: "GameState") -> str:
        players = game_state.players
        print(f"{player.name}, choose a number:")
        print("0: Look at two center cards")
        for i, p in enumerate(players, 1):
            if p != player:
                print(f"{i}: Look at {p.name}'s card")
        
        choice = int(input("Enter your choice: "))
        if choice == 0:
            cards = random.sample(game_state.center_cards, max(2, len(game_state.center_cards)))
            return f"You see the following center cards: {cards[0].name}, {cards[1].name}"
        elif 1 <= choice <= len(players):
            target = players[choice - 1]
            return f"You see that {target.name}'s role is: {target.role.name}"
        else:
            return "Invalid choice. You lose your night action."

class Robber(Role):
    def __init__(self):
        super().__init__("Robber")

    def night_action(self, player: "Player", game_state: "GameState") -> str:
        players = game_state.players
        print(f"{player.name}, choose a player to rob:")
        for i, p in enumerate(players, 1):
            if p != player:
                print(f"{i}: Rob {p.name}")
        
        choice = int(input("Enter your choice: "))
        if 1 <= choice <= len(players):
            target = players[choice - 1]
            player.role, target.role = target.role, player.role
            return f"You swapped roles with {target.name}. Your new role is: {player.role.name}"
        else:
            return "Invalid choice. You lose your night action."

class Troublemaker(Role):
    def __init__(self):
        super().__init__("Troublemaker")

    def night_action(self, player: "Player", game_state: "GameState") -> str:
        players = game_state.players
        print(f"{player.name}, choose two players to swap roles:")
        for i, p in enumerate(players, 1):
            if p != player:
                print(f"{i}: {p.name}")
        
        choice1 = int(input("Enter the number of the first player: "))
        choice2 = int(input("Enter the number of the second player: "))
        
        if 1 <= choice1 <= len(players) and 1 <= choice2 <= len(players) and choice1 != choice2:
            player1 = players[choice1 - 1]
            player2 = players[choice2 - 1]
            player1.role, player2.role = player2.role, player1.role
            return f"You swapped the roles of {player1.name} and {player2.name}."
        else:
            return "Invalid choice. You lose your night action."

def assign_roles(players: List["Player"]) -> List[Role]:
    global_role_pool = [Werewolf(), Villager(), Seer(), Robber(), Troublemaker(), Villager(), Villager(), Villager()]
    role_pool_for_this_many_players = global_role_pool[:len(players)+3]

    roles = role_pool_for_this_many_players[:]
    random.shuffle(roles)
    
    for player, role in zip(players, roles[:len(players)]):
        player.set_role(role)

    return roles[len(players):]  # Return unused roles
