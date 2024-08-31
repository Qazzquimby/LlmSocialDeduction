import random

class Role:
    def __init__(self, name):
        self.name = name

    def night_action(self, player, game_state):
        pass

class Werewolf(Role):
    def __init__(self):
        super().__init__("Werewolf")

    def night_action(self, player, game_state):
        other_werewolves = [p for p in game_state.players if p != player and isinstance(p.role, Werewolf)]
        if other_werewolves:
            return f"You see that {', '.join(w.name for w in other_werewolves)} is/are also Werewolf/Werewolves."
        else:
            center_card = random.choice(game_state.center_cards)
            return f"You are the only Werewolf. You look at a center card and see: {center_card.name}"

class Villager(Role):
    def __init__(self):
        super().__init__("Villager")

class Seer(Role):
    def __init__(self):
        super().__init__("Seer")

    def night_action(self, player, game_state):
        choice = input(f"{player.name}, do you want to look at (1) two center cards or (2) another player's card? ")
        if choice == "1":
            cards = random.sample(game_state.center_cards, 2)
            return f"You see the following center cards: {cards[0].name}, {cards[1].name}"
        elif choice == "2":
            target = random.choice([p for p in game_state.players if p != player])
            return f"You see that {target.name}'s role is: {target.role.name}"
        else:
            return "Invalid choice. You lose your night action."

class Robber(Role):
    def __init__(self):
        super().__init__("Robber")

    def night_action(self, player, game_state):
        target = random.choice([p for p in game_state.players if p != player])
        player.role, target.role = target.role, player.role
        return f"You swapped roles with {target.name}. Your new role is: {player.role.name}"

def assign_roles(players):
    roles = [Werewolf(), Werewolf(), Villager(), Villager(), Seer(), Robber()]
    random.shuffle(roles)
    
    for player, role in zip(players, roles[:len(players)]):
        player.set_role(role)

    return roles[len(players):]  # Return unused roles
