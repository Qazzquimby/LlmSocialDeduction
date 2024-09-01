import random
from typing import List, Optional, TYPE_CHECKING
from roles import Role

if TYPE_CHECKING:
    from game_state import GameState

class Player:
    def __init__(self, name: str, agent_type: str = 'human'):
        self.name: str = name
        self.agent_type: str = agent_type
        self.role: Optional[Role] = None
        self.original_role: Optional[Role] = None
        self.observations: List[str] = []

    def set_role(self, role: Role) -> None:
        self.role = role
        self.original_role = role
        self.observations.append(f"Your initial role is {role.name}")

    def night_action(self, game_state: 'GameState') -> Optional[str]:
        if self.role:
            action_result = self.role.night_action(self, game_state)
            if action_result:
                self.observations.append(action_result)
            return action_result
        return None

    def speak(self) -> str:
        if self.agent_type == 'human':
            return self.human_speak()
        elif self.agent_type == 'random':
            return self.random_speak()
        else:
            raise ValueError(f"Unknown agent type: {self.agent_type}")

    def human_speak(self) -> str:
        print(f"\n{self.name}, here are your observations:")
        for i, obs in enumerate(self.observations, 1):
            print(f"{i}. {obs}")
        return input(f"{self.name} (Human), enter your message: ")

    def random_speak(self) -> str:
        messages = [
            "I think someone's lying!",
            "I'm pretty sure I'm telling the truth.",
            "Who do we suspect?",
            "I have a hunch about this...",
            "Let's think about this logically.",
        ]
        return f"{self.name} (Random AI): {random.choice(messages)}"

    def vote(self, players: List['Player']) -> 'Player':
        if self.agent_type == 'human':
            return self.human_vote(players)
        elif self.agent_type == 'random':
            return self.random_vote(players)
        else:
            raise ValueError(f"Unknown agent type: {self.agent_type}")

    def human_vote(self, players: List['Player']) -> 'Player':
        print(f"\n{self.name}, here are your observations:")
        for i, obs in enumerate(self.observations, 1):
            print(f"{i}. {obs}")
        
        while True:
            print("\nAvailable players to vote for:")
            for i, player in enumerate(players, 1):
                if player != self:
                    print(f"{i}. {player.name}")
            try:
                choice = int(input(f"{self.name}, enter the number of the player you want to vote for: "))
                if 1 <= choice <= len(players) and players[choice-1] != self:
                    return players[choice-1]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

    def random_vote(self, players: List['Player']) -> 'Player':
        return random.choice([p for p in players if p != self])
