import random
from typing import List, Optional
from .core import Prompt
from games.one_night_ultimate_werewolf.roles import Role
from .game_state import GameState

class Player:
    def __init__(self, game, name: str):
        self.game = game
        self.name: str = name
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
        raise NotImplementedError

    def vote(self, players: List['Player']) -> 'Player':
        other_players = [other_player for other_player in players if other_player != self]
        question = "Which player do you want to vote to execute?"
        for i, player in enumerate(other_players):
            question += f"\n{i}: {player.name}"

        vote = self.get_choice(question)
        if vote:
            return players[vote[0]]
        else:
            return random.choice(players)

    def get_choice(self, prompt: str) -> List[int]:
        raise NotImplementedError

    def prompt_with(self, prompt: str) -> str:
        raise NotImplementedError

    def think(self):
        raise NotImplementedError

    def handle_action(self, action: str, game_state: 'GameState') -> str:
        if action == 'night_action':
            return self.night_action(game_state)
        elif action == 'speak':
            return self.speak()
        elif action.startswith('vote:'):
            target_name = action.split(':')[1]
            target = next(p for p in game_state.players if p.name == target_name)
            return f"{self.name} voted for {target.name}"
        else:
            return f"Invalid action: {action}"

    def __str__(self):
        return self.name

class HumanPlayer(Player):
    def speak(self) -> str:
        message = input("What would you like to say to the other players? ")
        return f"Human: {message}"

    def get_choice(self, prompt: str) -> List[int]:
        print("\nCurrent observations:")
        for message in self.observations:
            print(message)
        choice = input(prompt + "\nEnter your choice: ")
        return [int(choice)]

    def prompt_with(self, prompt: str) -> str:
        print("\nCurrent observations:")
        for message in self.observations:
            print(message)
        return input(prompt)

    def think(self):
        print("\nTime to think about your strategy. Press Enter when you're ready to continue.")
        input()

class AIPlayer(Player):
    def __init__(self, game, name: str, model):
        super().__init__(game, name)
        self.model = model
        self.total_cost = 0

    def speak(self) -> str:
        prompt = "What would you like to say to the other players? Your entire response will be broadcast so don't say anything you don't want them to hear. Keep it brief and focused."
        message = self.prompt_with(prompt)
        return f"{self.name}: {message}"

    def get_choice(self, prompt: str) -> List[int]:
        response = self.prompt_with(prompt + "\nFormat your answer as a single number.")
        try:
            return [int(response)]
        except ValueError:
            return []

    def prompt_with(self, prompt: str) -> str:
        litellm_prompt = Prompt().add_message(
            f"You're playing a social deduction game. Your name is {self.name}", role="system"
        )

        for message in self.observations:
            litellm_prompt = litellm_prompt.add_message(message, role="system")

        litellm_prompt = litellm_prompt.add_message(prompt, role="user")
        response = litellm_prompt.run(model=self.model, should_print=False)
        self.total_cost += litellm_prompt.total_cost

        self.observations.append(f"I was asked: {prompt}\n\nI responded: {response}\n")

        return response

    def think(self):
        self.prompt_with(
            "Think privately about your strategy. What seems wise? What can you logically deduce from your observations? How can you gain more information, build trust, or mislead your opponents?"
        )
