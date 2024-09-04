import random
from typing import List, Optional, TYPE_CHECKING
from core import Prompt
from roles import Role

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
                 .split(" "))

        numbers = [int(word) for word in words if word.isnumeric()]
        return numbers

    def prompt_with(self, prompt: str) -> str:
        raise NotImplementedError("Subclass must implement abstract method")

    def think(self):
        raise NotImplementedError


class HumanPlayer(Player):
    def speak(self) -> str:
        message = self.prompt_with(
            "What would you like to say to the other players? Your entire response will be broadcast so don't say anything you don't want them to hear. Keep it brief and don't teach basic strategy."
        )
        return message

    def prompt_with(self, prompt: str) -> str:
        print("\n\n\n\n\n\n-------------\nCurrent observations:\n")
        for message in self.observations:
            print(message+"\n\n")
        return input(prompt)

    def think(self):
        pass



class AIPlayer(Player):
    def __init__(self, name: str, model, personality: str = None):
        super().__init__(name)
        self.model=model
        self.personality = personality

        self.total_cost = 0
        self.games_played = 0
        self.games_won = 0

    def speak(self) -> str:
        message = self.prompt_with("What would you like to say to the other players? Your entire response will be broadcast so don't say anything you don't want them to hear. Keep it brief.")
        return f"{self.name}({self.model}): {message}"

    def prompt_with(self, prompt: str) -> str:
        litellm_prompt = Prompt().add_message(
            f"You're playing a social deduction game. Your name is {self.name}", role="system"
        )

        litellm_prompt.add_message("""Rules:       
        Each player has a role, but that role may be changed during the night phase. Three more roles are in the center.
        
        First there is a night phase where certain roles will act.
        Werewolves will see the identities of other werewolves.
        The seer will see the identities of another player or two of the unused identities.
        The robber may steal a player's card and see what it is.
        The troublemaker may swap two other players' cards without seeing them.
        There are no other roles and no other ways to gain information.
        
        During the day, each player will vote for someone to execute. The player with the most votes will be executed.
        If a werewolf is executed, everyone not on the werewolf team wins.
        If there is a werewolf in the game and they are not executed, the werewolf team wins.
        
        Perhaps obvious, werewolves should lie about who they are and invent a misleading cover identity with made up observations.
        """)

        for message in self.observations:
            litellm_prompt = litellm_prompt.add_message(message, role="system")

        if self.personality:
            litellm_prompt = litellm_prompt.add_message(f"Your personality is: {self.personality}", role="system")

        litellm_prompt = litellm_prompt.add_message(prompt, role="system")
        response = litellm_prompt.run(model=self.model, should_print=False)
        self.total_cost += litellm_prompt.total_cost

        self.observations.append(f"I was asked: {prompt}\n\n I responded: {response}\n\n\n")

        return response

    def think(self):
        self.prompt_with(
            """Think privately. Your response is for you and you alone, so use whatever format is best for you. 
                    Think step by step. What strategy seems wise? What can you logically induce from your observations? How can you gain more information, built trust, or mislead your opponents?
                    """
        )
