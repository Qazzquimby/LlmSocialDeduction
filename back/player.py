import random
from typing import List, Optional, TYPE_CHECKING
from core import Prompt
from onuw_roles import Role

if TYPE_CHECKING:
    from game_state import GameState


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
        other_players = [other_player for other_player in players if
                         other_player != self]
        question = "Which player do you want to vote to execute?"
        for i, player in enumerate(other_players):
            question += f"\n{i}: {player.name}"

        vote = self.get_choice(question)
        if vote:
            return players[vote[0]]
        else:
            return random.choice(players)

    def get_choice(self, prompt: str) -> List[int]:
        response = self.prompt_with(
            prompt + "\n Format: Step by step thinking, then {choice_number, choice name, why you chose that option instead of the others}.")

        formatted_answer = response.split("{")[-1]
        words = (formatted_answer
                 .replace(",", " ")
                 .replace('"', " ")
                 .replace("'", " ")
                 .replace(".", " ")
                 .replace("*", " ")
                 .replace(":", " ")
                 .replace("}", " ")
                 .split(" "))

        numbers = [int(word) for word in words if word.isnumeric()]
        return numbers

    def prompt_with(self, prompt: str) -> str:
        raise NotImplementedError

    def think(self):
        raise NotImplementedError

    def __str__(self):
        return self.name


class HumanPlayer(Player):
    def speak(self) -> str:
        message = self.prompt_with(
            "What would you like to say to the other players? Your entire response will be broadcast so don't say anything you don't want them to hear. Keep it brief and don't teach basic strategy."
        )
        return f"Human: {message}"

    def prompt_with(self, prompt: str) -> str:
        print("\n\n\n\n\n\n-------------\nCurrent observations:\n")
        for message in self.observations:
            print(message + "\n\n")
        return input(prompt)

    def think(self):
        pass


class AIPlayer(Player):
    def __init__(self, game, name: str, model, personality: str = None):
        super().__init__(game, name)
        self.model = model
        self.personality = personality

        self.total_cost = 0
        self.games_played = 0
        self.games_won = 0

    def speak(self) -> str:
        prompt = ""
        if self.personality:
            prompt += f"\nYour personality is: {self.personality}"
        prompt += "What would you like to say to the other players? Your entire response will be broadcast so don't say anything you don't want them to hear. Keep it brief and focused."

        message = self.prompt_with(prompt)
        return f"{self.name}({self.model}): {message}"

    def prompt_with(self, prompt: str) -> str:
        litellm_prompt = Prompt().add_message(
            f"You're playing a social deduction game. Your name is {self.name}",
            role="system"
        )

        rules = "Rules:\n"
        rules += "Each player has a role, but that role may be changed during the night phase. Three more roles are in the center.\n\n"
        rules += "First there is a night phase where certain roles will act.\n"

        for role in set(player.role.__class__ for player in self.game.players):
            rules += role().get_rules() + "\n"

        rules += "\nDuring the day, each player will vote for someone to execute. The player with the most votes will be executed.\n"

        litellm_prompt.add_message(rules)

        for message in self.observations:
            litellm_prompt = litellm_prompt.add_message(message, role="system")

        litellm_prompt = litellm_prompt.add_message(prompt, role="system")
        response = litellm_prompt.run(model=self.model, should_print=False)
        self.total_cost += litellm_prompt.total_cost

        self.observations.append(
            f"I was asked: {prompt}\n\n I responded: {response}\n\n\n")

        return response

    def think(self):
        self.prompt_with(
            """Think privately. Your response is for you and you alone, so use whatever format is best for you. 
                    Think step by step. What strategy seems wise? What can you logically induce from your observations? How can you gain more information, built trust, or mislead your opponents?
                    """
        )
