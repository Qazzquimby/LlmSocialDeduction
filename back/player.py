import random
from typing import List, Optional, TYPE_CHECKING, Type
from core import Prompt
from roles import Role

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

    def get_choice(self, prompt: str, choose_multiple=False) -> List[int]:
        if choose_multiple:
            response = self.prompt_with(
                prompt + "\n Your final answer must take the form {choice_numbers, choice names}, eg {1 3, Bob Clyde}."
            )
        else:
            response = self.prompt_with(
                prompt + "\n Your final answer must take the form {choice_number, choice name}, eg {1, Bob}."
            )

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
            "What would you like to say to the other players? Your entire response will be broadcast so don't say anything you don't want them to hear."
        )
        return f"Human: {message}"

    def prompt_with(self, prompt: str) -> str:
        print("\n\n\n\n\n\n-------------\nCurrent observations:\n")
        print(get_rules(self.game.game_state.role_pool))
        for message in self.observations:
            print(message + "\n\n")
        return input(prompt)

    def think(self):
        pass

def get_rules(roles: List[Role]) -> str:
    rules = "Rules:\n"
    rules += "Each player has a role, but that role may be changed during the night phase. Three more roles are in the center.\n\n"
    rules += ("First there is a night phase where certain roles will act.\n"
              "Players may have their roles changed during the night, but they'll perform their original role's action in the night anyway. Usually a player has no way of knowing if their role changed.\n"
              "Roles activate in the order they're described below.")

    seen_roles = set()
    for role in roles:
        if role not in seen_roles:
            seen_roles.add(role)
            rules += role.get_rules() + "\n"

    rules += "\nDuring the day, each player will vote for someone to execute. The players with the most votes (all on a tie) will be executed. Werewolves win if no werewolf is executed. Other roles win if a werewolf to be executed unless their rules say otherwise.\n"
    rules += "Then the game is over and winners are determined. There is only one round."
    return rules

class AIPlayer(Player):
    def __init__(self, game, name: str, model, personality: str = None):
        super().__init__(game, name)
        self.model = model
        self.personality = personality

        self.total_cost = 0
        self.games_played = 0
        self.games_won = 0

        self.think_prompt = """First think step by step in point form. 
                What do you believe, how strongly, and why?
                What can you logically induce from your observations? What looks like misdirection?
                                   
                Should your strategy change given new information?
                
                Then answer the following question in the correct {} format:\n"""

    def speak(self) -> str:
        prompt = ""
        if self.personality:
            prompt += f"\nYour personality is: {self.personality}. Don't over do it, focus on the game."
        prompt += "What would you like to say to the other players? After thinking, enter your message between curly brackets like {This is my message.} Keep it focused on logical reasoning. Try to accomplish something with your message, rather than passing. Other players will expect you to tell your role and observations and you will look suspicious if you don't."

        response = self.prompt_with(prompt, should_think=True)
        message_to_broadcast = response.split("{")[-1]
        message_to_broadcast = message_to_broadcast.replace("}", "")
        return f"{self.name}({self.model}): {message_to_broadcast}"

    def prompt_with(self, prompt: str, should_think=False) -> str:
        litellm_prompt = Prompt().add_message(
            f"You're playing a social deduction game. Your name is {self.name}",
            role="system"
        )

        rules = get_rules(self.game.game_state.role_pool)

        litellm_prompt.add_message(rules, role="system")

        for message in self.observations:
            litellm_prompt = litellm_prompt.add_message(message, role="system")

        if should_think:
            prompt = self.think_prompt + prompt

        litellm_prompt = litellm_prompt.add_message(prompt, role="system")
        response = litellm_prompt.run(model=self.model, should_print=False)
        self.total_cost += litellm_prompt.total_cost

        self.observations.append(
            f"I was asked: {prompt}\n\n I responded: {response}\n\n\n")

        return response

    def think(self):
        raise DeprecationWarning("Removing this")
        self.prompt_with(
            """Think step by step in point form. 
                What do you believe, how strongly, and why?
                What can you logically induce from your observations? What looks like misdirection?
                                   
                Should your strategy change given new information?
                    """
        )
