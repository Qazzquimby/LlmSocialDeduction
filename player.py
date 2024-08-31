import random

class Player:
    def __init__(self, name, agent_type='human'):
        self.name = name
        self.agent_type = agent_type
        self.role = None
        self.original_role = None

    def set_role(self, role):
        self.role = role
        self.original_role = role

    def night_action(self, game_state):
        if self.role:
            return self.role.night_action(self, game_state)
        return None

    def speak(self):
        if self.agent_type == 'human':
            return self.human_speak()
        elif self.agent_type == 'random':
            return self.random_speak()
        else:
            raise ValueError(f"Unknown agent type: {self.agent_type}")

    def human_speak(self):
        return input(f"{self.name} (Human), enter your message: ")

    def random_speak(self):
        messages = [
            "I think someone's lying!",
            "I'm pretty sure I'm telling the truth.",
            "Who do we suspect?",
            "I have a hunch about this...",
            "Let's think about this logically.",
        ]
        return f"{self.name} (Random AI): {random.choice(messages)}"

    def vote(self, players):
        if self.agent_type == 'human':
            return self.human_vote(players)
        elif self.agent_type == 'random':
            return self.random_vote(players)
        else:
            raise ValueError(f"Unknown agent type: {self.agent_type}")

    def human_vote(self, players):
        while True:
            print("\nAvailable players to vote for:")
            for i, player in enumerate(players):
                if player != self:
                    print(f"{i + 1}. {player.name}")
            try:
                choice = int(input(f"{self.name}, enter the number of the player you want to vote for: ")) - 1
                if 0 <= choice < len(players) and players[choice] != self:
                    return players[choice]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

    def random_vote(self, players):
        return random.choice([p for p in players if p != self])
