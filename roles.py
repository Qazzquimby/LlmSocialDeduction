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
        other_werewolves = [p for p in game_state.players if
                            p != player and isinstance(p.role, Werewolf)]
        other_werewolves_names = ", ".join(
            w.name for w in other_werewolves) if other_werewolves else "no one"
        return f"You see that {other_werewolves_names} is/are also Werewolf/Werewolves."


class Villager(Role):
    def __init__(self):
        super().__init__("Villager")


class Seer(Role):
    def __init__(self):
        super().__init__("Seer")

    def night_action(self, player: "Player", game_state: "GameState") -> str:
        players = game_state.players
        options = "0: Look at two center cards\n" + "\n".join(
            [f"{i}: Look at {p.name}'s card" for i, p in enumerate(players, 1) if
             p != player])
        prompt = f"{player.name}, choose a number:\n{options}\nEnter your choice:"
        choice = player.get_choice(prompt)

        if choice[0] == 0:
            cards = game_state.center_cards[:2]
            return f"You see the following center cards: {cards[0].name}, {cards[1].name}"
        elif 1 <= choice[0] <= len(players):
            target = players[choice[0] - 1]
            return f"You see that {target.name}'s role is: {target.role.name}"
        else:
            return "Invalid choice. You lose your night action."


class Robber(Role):
    def __init__(self):
        super().__init__("Robber")

    def night_action(self, player: "Player", game_state: "GameState") -> str:
        players = game_state.players
        options = "\n".join(
            [f"{i}: Rob {p.name}" for i, p in enumerate(players, 1) if p != player])
        prompt = f"{player.name}, choose a player to rob:\n{options}\nEnter your choice:"
        choice = player.get_choice(prompt)

        if 1 <= choice[0] <= len(players):
            target = players[choice[0] - 1]
            player.role, target.role = target.role, player.role
            return f"You swapped roles with {target.name}. Your new role is: {player.role.name}"
        else:
            return "Invalid choice. You lose your night action."


class Troublemaker(Role):
    def __init__(self):
        super().__init__("Troublemaker")

    def night_action(self, player: "Player", game_state: "GameState") -> str:
        players = game_state.players
        options = "\n".join(
            [f"{i}: {p.name}" for i, p in enumerate(players, 1) if p != player])
        prompt = f"{player.name}, choose two players to swap roles:\n{options}\nEnter the choices numbers of both players separated by a space, like `2 3`:"
        choices = player.get_choice(prompt)

        if len(choices) == 2 and 1 <= choices[0] <= len(players) and 1 <= choices[
            1] <= len(players) and choices[0] != choices[1]:
            player1 = players[choices[0] - 1]
            player2 = players[choices[1] - 1]
            player1.role, player2.role = player2.role, player1.role
            return f"You swapped the roles of {player1.name} and {player2.name}."
        else:
            return "Invalid choice. You lose your night action."


def get_roles_in_game(num_players: int) -> List[Role]:
    global_role_pool = [
        Werewolf(), Werewolf(),
        Seer(), Robber(), Troublemaker(),
        Villager(), Villager(), Villager(), Villager()
    ]
    role_pool_for_this_many_players = global_role_pool[:num_players + 3]
    return role_pool_for_this_many_players


def assign_roles(players: List["Player"], roles_in_game: List[Role]) -> List[Role]:
    roles = roles_in_game[:]
    random.shuffle(roles)

    for player, role in zip(players, roles[:len(players)]):
        player.set_role(role)

    return roles[len(players):]  # Return unused roles
