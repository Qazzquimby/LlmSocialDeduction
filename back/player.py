import asyncio
import random
from typing import Optional, TYPE_CHECKING

from loguru import logger

from message_types import (
    BaseEvent,
    BaseMessage,
    PlayerActionMessage,
    RulesError,
)
from typing import List
from core import Prompt
from roles import Role

from aioconsole import ainput

from websocket_management import UserLogin

if TYPE_CHECKING:
    from game_state import GameState


class Player:
    def __init__(self, game, name: str):
        self.game = game
        self.name: str = name
        self.role: Optional[Role] = None
        self.original_role: Optional[Role] = None
        self.observations: List[BaseEvent] = []

    async def set_role(self, role: Role) -> None:
        self.role = role
        self.original_role = role
        await self.observe(
            PlayerActionMessage(
                message=f"Your initial role is {role.name}",
                player=self.name,
                action="role_assignment",
            )
        )

    async def night_action(self, game_state: "GameState") -> Optional[str]:
        if self.role:
            action_result = await self.original_role.night_action(self, game_state)
            if action_result:
                await self.observe(
                    PlayerActionMessage(
                        message=action_result, player=self.name, action="night_action"
                    )
                )
            return action_result
        return None

    async def speak(self) -> str:
        raise NotImplementedError

    async def vote(self, players: List["Player"]) -> "Player":
        other_players = [
            other_player for other_player in players if other_player != self
        ]
        question = "Which player do you want to vote to execute?"
        choices = [(i, player.name) for i, player in enumerate(other_players)]

        vote = await self.get_choice(question, choices)
        return other_players[vote[0]]

    async def get_choice(
        self, prompt: str, choices: List[tuple], choose_multiple=False
    ) -> List[int]:
        choice_prompt = prompt + "\n"
        for i, (choice, description) in enumerate(choices):
            choice_prompt += f"{i}: {description}\n"

        if choose_multiple:
            choice_prompt += "\nYour final answer must take the form {choice_numbers, choice names}, eg {1 3, Bob Clyde}."
        else:
            choice_prompt += "\nYour final answer must take the form {choice_number, choice name}, eg {1, Bob}."

        response = await self.prompt_with(choice_prompt, should_think=True)

        formatted_answer = response.split("{")[-1]
        words = (
            formatted_answer.replace(",", " ")
            .replace('"', " ")
            .replace("'", " ")
            .replace(".", " ")
            .replace("*", " ")
            .replace(":", " ")
            .replace("}", " ")
            .split(" ")
        )

        numbers = [int(word) for word in words if word.isnumeric()]

        valid_choices = list(range(len(choices)))
        numbers = [num for num in numbers if num in valid_choices]

        if not numbers:
            # If no valid choice was made, pick a random valid choice
            random_choice = random.choice(valid_choices)
            await self.observe(
                BaseMessage(
                    type="Invalid input",
                    message=f"Invalid choice. Randomly chose {random_choice}",
                )
            )
            return [random_choice]

        return numbers

    async def prompt_with(self, prompt: str, should_think=False) -> str:
        raise NotImplementedError

    async def observe(self, event: BaseEvent):
        self.observations.append(event)

    def __str__(self):
        return self.name


class HumanPlayer(Player):
    def __init__(self, game, name):
        super().__init__(game, name)

    async def set_role(self, role: Role) -> None:
        await super().set_role(role)

    async def speak(self) -> str:
        message = await self.prompt_with(
            "What would you like to say to the other players?"
        )
        return f"{message}"

    async def observe(self, event: BaseEvent):
        await super().observe(event)
        await self.print(event)

    async def print(self, event: BaseEvent):
        raise NotImplementedError

    async def prompt_with(
        self, prompt: str, should_think=False, params: dict = None
    ) -> str:
        raise NotImplementedError


class LocalHumanPlayer(HumanPlayer):
    async def prompt_with(
        self, prompt: str, should_think=False, params: dict = None
    ) -> str:
        return await ainput(prompt)

    async def print(self, event: BaseEvent):
        if isinstance(event, BaseMessage):
            print(event.message)
        else:
            print(f"Event: {event.type}")


import time
from message_types import PromptMessage
from websocket_management import websocket_manager


class WebHumanPlayer(HumanPlayer):
    def __init__(self, game, login: UserLogin):
        super().__init__(game, login.name)
        self.login = login
        self.user_id = login.user_id
        self.last_activity = time.time()

    async def prompt_with(
        self, prompt: str, should_think=False, params: dict = None
    ) -> str:
        logger.info(f"prompting {self.login.name} with {prompt[:20]}")
        prompt_event = PromptMessage(message=prompt, username="System")
        return await websocket_manager.get_input(self.user_id, prompt_event)

    async def print(self, event: BaseEvent):
        logger.info(f"informing {self.login.name} with {event}")
        await websocket_manager.send_personal_message(event, self.user_id)

    def update_activity(self):
        self.last_activity = time.time()


def get_rules(roles: List[Role]) -> str:
    rules = "Rules:\n"
    rules += "Each player has a role, but that role may be changed during the night phase. Three more roles are in the center.\n\n"
    rules += (
        "First there is a night phase where certain roles will act.\n"
        "Players may have their roles changed during the night, but they'll perform their original role's action in the night anyway. Usually a player has no way of knowing if their role changed.\n"
        "Roles activate in the order they're described below."
    )

    seen_roles = set()
    for role in sorted(roles, key=lambda r: r.wake_order):
        if role not in seen_roles:
            seen_roles.add(role)
            rules += role.get_rules() + "\n"

    rules += "\nDuring the day, each player will vote for someone to execute. The players with the most votes (all on a tie) will be executed. Werewolves win if no werewolf is executed. Other roles win if a werewolf to be executed unless their rules say otherwise.\n"
    rules += (
        "Then the game is over and winners are determined. There is only one round."
    )
    return rules


from typing import Optional
import os


class AIPlayer(Player):
    def __init__(
        self,
        game,
        name: str,
        model,
        api_key: Optional[str] = None,
        personality: str = None,
    ):
        super().__init__(game, name)
        self.model = model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.personality = personality

        self.total_cost = 0
        self.games_played = 0
        self.games_won = 0

        self.think_prompt = """First think step by step in point form. 
                What do you believe, how strongly, and why?
                What can you logically induce from your observations? Quote relevant the relevant rules and double check your reasoning. 
                                                   
                Should your strategy change given new information?
                
                Then answer the following question in the correct {} format:\n"""

        self.use_mock_api = os.environ.get("USE_MOCK_API", "false").lower() == "true"

    async def speak(self) -> str:
        prompt = ""
        if self.personality:
            prompt += f"\nYour personality is: {self.personality} Don't over do it, focus on the game.\n"
        prompt += "What would you like to say to the other players? After thinking, enter your message between curly brackets like {This is my message.} Keep it focused on logical reasoning. Be intentional about what you share - don't self incriminate. Try to *accomplish* something with your message, don't pass or be scared of risk. Other players will expect you to tell your role and observations and you will look suspicious if you don't. If you say you're a role, they'll expect you to have the information that role would have. If you say you have information, they will expect your role to back it up. Don't say you have a hunch or feeling, make claims."

        response = await self.prompt_with(
            prompt, should_think=True, should_rules_check=True
        )
        message_to_broadcast = response.split("{")[-1]
        message_to_broadcast = message_to_broadcast.replace("}", "")
        return f"{message_to_broadcast}"

    async def prompt_with(
        self, prompt: str, should_think=False, should_rules_check=False
    ) -> str:
        litellm_prompt = Prompt().add_message(
            f"You're playing a social deduction game. Your name is {self.name}",
            role="system",
        )

        rules = get_rules(self.game.state.role_pool)

        litellm_prompt.add_message(rules, role="system")

        for observation in self.observations:
            if isinstance(observation, BaseMessage):
                litellm_prompt = litellm_prompt.add_message(
                    observation.message, role="system"
                )
            else:
                litellm_prompt = litellm_prompt.add_message(
                    str(observation.model_dump()), role="system"
                )

        if should_think:
            prompt = self.think_prompt + prompt

        litellm_prompt = litellm_prompt.add_message(prompt, role="system")
        response = await self.prompt_model(litellm_prompt)

        await self.observe(
            BaseMessage(
                type="my_action",
                message=f"I was asked: {prompt}\n\n I responded: {response}\n\n\n",
            )
        )

        if should_rules_check:
            await self.check_rules(response)

        return response

    async def check_rules(self, message: str) -> None:
        rules = get_rules(self.game.state.role_pool)
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

        response = await self.prompt_model(
            litellm_prompt=Prompt().add_message(prompt, role="system")
        )

        if "No errors found" not in response:
            part_to_share = response.split("{")[-1]
            part_to_share = part_to_share.replace("}", "")
            await self.observe(
                RulesError(
                    message=(
                        f"Rules Genie: Hi, I might have noticed a rules error in your last message. If this was intentional (or *I* am mistaken), just ignore me. It's also fine to pretend to make a rules error when talking.\n"
                        f"{part_to_share}"
                    ),
                )
            )

    async def prompt_model(self, litellm_prompt: Prompt):
        if self.use_mock_api:
            return self.mock_api_response(litellm_prompt)

        response = litellm_prompt.run(
            model=self.model, api_key=self.api_key, should_print=False
        )
        self.total_cost += litellm_prompt.total_cost
        return response

    def mock_api_response(self, litellm_prompt: Prompt) -> str:
        return f"Mock response."


async def everyone_observe(players: List[Player], event: BaseEvent):
    await asyncio.gather(*[player.observe(event) for player in players])
