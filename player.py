from typing import List, Optional, TYPE_CHECKING

from core import Prompt
from roles import Role
from prompt_utils import prompt_agent

if TYPE_CHECKING:
    from game_state import GameState

class Player:
    def __init__(self, name: str):
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
        raise NotImplementedError("Subclass must implement abstract method")

    def vote(self, players: List['Player']) -> 'Player':
        raise NotImplementedError("Subclass must implement abstract method")

    def get_choice(self, prompt: str) -> List[int]:
        response = self.prompt_with(prompt + "\n Format: Step by step thinking, then {choice_number, choice name, why you chose that option instead of the others}.")

        formatted_answer = response.split("{")[-1]
        words = (formatted_answer
                 .replace(",", " ")
                 .replace('"', " ")
                 .replace("'", " ")
                 .replace(".", " ")
                 .split(" "))

        numbers = [int(word) for word in words if word.isnumeric()]
        return numbers

    def prompt_with(self, prompt: str) -> str:
        raise NotImplementedError("Subclass must implement abstract method")

class HumanPlayer(Player):
    def speak(self) -> str:
        observations = "\n".join([f"{i}. {obs}" for i, obs in enumerate(self.observations, 1)])
        prompt = f"{self.name}, here are your observations:\n{observations}\nBased on these observations, what would you like to say?"
        return prompt_agent(prompt)

    def vote(self, players: List['Player']) -> 'Player':
        observations = "\n".join([f"{i}. {obs}" for i, obs in enumerate(self.observations, 1)])
        available_players = "\n".join([f"{i}. {player.name}" for i, player in enumerate(players, 1) if player != self])
        prompt = f"{self.name}, here are your observations:\n{observations}\n\nAvailable players to vote for:\n{available_players}\nBased on your observations, which player number do you want to vote for?"
        
        while True:
            choice = prompt_agent(prompt)
            try:
                choice = int(choice)
                if 1 <= choice <= len(players) and players[choice-1] != self:
                    return players[choice-1]
                else:
                    prompt = "Invalid choice. Please try again. Which player number do you want to vote for?"
            except ValueError:
                prompt = "Please enter a valid number. Which player number do you want to vote for?"

    def prompt_with(self, prompt: str) -> str:
        return input(prompt)

class AIPlayer(Player):
    def speak(self) -> str:
        message = self.prompt_with("What would you like to say to the other players?")
        return f"{self.name}(AI): {message}"

    def vote(self, players: List['Player']) -> 'Player':
        other_players = [other_player for other_player in players if other_player != self]
        question = "Which player do you want to vote to execute?"
        for i, player in enumerate(other_players):
            question += f"\n{i}: {player.name}"

        vote = self.get_choice(question)
        return players[vote[0]]

    def prompt_with(self, prompt: str) -> str:
        litellm_prompt = Prompt().add_message(
            "You're playing a social deduction game.", role="system"
        )

        # todo add rules

        litellm_prompt = litellm_prompt.add_message(
            "Your past observations are:", role="system"
        )
        for message in self.observations:
            litellm_prompt = litellm_prompt.add_message(message, role="system")

        litellm_prompt = litellm_prompt.add_message(prompt, role="system")
        response = litellm_prompt.run()

        self.observations.append(f"I am asked {prompt}\n\n I respond{response}\n\n\n")

        return response