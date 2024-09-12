import random
from typing import List, Optional, TYPE_CHECKING
from core import Prompt
from roles import Role

from aioconsole import ainput

if TYPE_CHECKING:
    from game_state import GameState


class Player:
    def __init__(self, game, name: str):
        self.game = game
        self.name: str = name
        self.role: Optional[Role] = None
        self.original_role: Optional[Role] = None
        self.observations: List[str] = []

    async def set_role(self, role: Role) -> None:
        self.role = role
        self.original_role = role
        await self.observe(f"Your initial role is {role.name}")

    async def night_action(self, game_state: 'GameState') -> Optional[str]:
        if self.role:
            action_result = await self.original_role.night_action(self, game_state)
            if action_result:
                await self.observe(action_result)
            return action_result
        return None

    async def speak(self) -> str:
        raise NotImplementedError

    async def vote(self, players: List['Player']) -> 'Player':
        other_players = [other_player for other_player in players if
                         other_player != self]
        question = "Which player do you want to vote to execute?"
        for i, player in enumerate(other_players):
            question += f"\n{i}: {player.name}"

        vote = await self.get_choice(question)
        if vote:
            return players[vote[0]]
        else:
            return random.choice(players)

    async def get_choice(self, prompt: str, choose_multiple=False) -> List[int]:
        if choose_multiple:
            response = await self.prompt_with(
                prompt + "\n Your final answer must take the form {choice_numbers, choice names}, eg {1 3, Bob Clyde}.",
                should_think=True
            )
        else:
            response = await self.prompt_with(
                prompt + "\n Your final answer must take the form {choice_number, choice name}, eg {1, Bob}.",
                should_think=True
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

    async def prompt_with(self, prompt: str, should_think=False) -> str:
        raise NotImplementedError

    async def observe(self, message):
        self.observations.append(message)

    def __str__(self):
        return self.name


class HumanPlayer(Player):
    def __init__(self, game, name):
        super().__init__(game, name)

    async def set_role(self, role: Role) -> None:
        await self.observe(
            get_rules(self.game.game_state.role_pool)
            # todo add types to observations
        )

        await super().set_role(role)

    async def speak(self) -> str:
        message = await self.prompt_with(
            "What would you like to say to the other players?"
        )
        return f"Human: {message}"

    async def observe(self, message):
        self.observations.append(message)
        await self.print(message)

    async def print(self, message):
        raise NotImplementedError

    async def prompt_with(self, prompt: str, should_think=False) -> str:
        raise NotImplementedError

class LocalHumanPlayer(HumanPlayer):
    async def prompt_with(self, prompt: str, should_think=False) -> str:
        return await ainput(prompt)

    async def print(self, message):
        print(message)

class WebHumanPlayer(HumanPlayer):
    def __init__(self, game, name: str, websocket):
        super().__init__(game, name)
        self.websocket = websocket

    async def prompt_with(self, prompt: str, should_think=False) -> str:
        await self.websocket.send_json({"type": "prompt", "message": prompt})
        response = await self.websocket.receive_json()
        return response['message']

    async def print(self, message):
        await self.websocket.send_json({"type": "untyped", "message": message})


def get_rules(roles: List[Role]) -> str:
    rules = "Rules:\n"
    rules += "Each player has a role, but that role may be changed during the night phase. Three more roles are in the center.\n\n"
    rules += ("First there is a night phase where certain roles will act.\n"
              "Players may have their roles changed during the night, but they'll perform their original role's action in the night anyway. Usually a player has no way of knowing if their role changed.\n"
              "Roles activate in the order they're described below.")

    seen_roles = set()
    for role in sorted(roles, key=lambda r: r.wake_order):
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
                What can you logically induce from your observations? Quote relevant the relevant rules and double check your reasoning. 
                                                   
                Should your strategy change given new information?
                
                Then answer the following question in the correct {} format:\n"""

    async def speak(self) -> str:
        prompt = ""
        if self.personality:
            prompt += f"\nYour personality is: {self.personality} Don't over do it, focus on the game.\n"
        prompt += "What would you like to say to the other players? After thinking, enter your message between curly brackets like {This is my message.} Keep it focused on logical reasoning. Be intentional about what you share - don't self incriminate. Try to *accomplish* something with your message, don't pass or be scared of risk. Other players will expect you to tell your role and observations and you will look suspicious if you don't. If you say you're a role, they'll expect you to have the information that role would have. If you say you have information, they will expect your role to back it up. Don't say you have a hunch or feeling, make claims."

        response = await self.prompt_with(prompt, should_think=True, should_rules_check=True)
        message_to_broadcast = response.split("{")[-1]
        message_to_broadcast = message_to_broadcast.replace("}", "")
        return f"{self.name}({self.model}): {message_to_broadcast}"

    async def prompt_with(self, prompt: str, should_think=False, should_rules_check=False) -> str:
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

        await self.observe(
            f"I was asked: {prompt}\n\n I responded: {response}\n\n\n")

        if should_rules_check:
            await self.check_rules(response)

        return response

    async def check_rules(self, message: str) -> None:
        rules = get_rules(self.game.game_state.role_pool)
        prompt = f"""
        You are a Rules Genie for a social deduction game. 
        Your job is to check if a player's statement contains rules errors or faulty reasoning. 
    
        {rules}
    
        Player's statement:
        {message}
    
        For each logical or rules statement the player made while thinking, determine if it is solid reasoning step by step while quoting the relevant original rules. It's normal for player's to lie to each other while speaking, so only report errors if you think they're unintentional. You can backtrack if you find you're making a mistake.
    
        When you're done reasoning, provide an answer in {{}} brackets.
        If the statement contains any errors, explain the errors in the brackets. If not, say '{{No errors found}}.'
        """

        litellm_prompt = Prompt().add_message(prompt, role="system")
        response = litellm_prompt.run(model=self.model, should_print=False)

        if "No errors found" not in response:
            part_to_share = response.split("{")[-1]
            part_to_share = part_to_share.replace("}", "")
            await self.observe(
                f"Rules Genie: Hi, I might have noticed a rules error in your last message. If this was intentional (or *I* am mistaken), just ignore me. It's also fine to pretend to make a rules error when talking.\n"
                f"{part_to_share}"
            )
