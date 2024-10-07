import asyncio
import random
from typing import Optional, TYPE_CHECKING, Tuple, Union

from loguru import logger

from message_types import (
    BaseEvent,
    BaseMessage,
    PlayerActionMessage,
    RulesError,
    PromptMessage,
    SpeechMessage,
    PromptChoice,
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

    async def speak(self, chat=False) -> str:
        raise NotImplementedError

    async def vote(self, players: List["Player"]) -> "Player":
        other_players = [
            other_player for other_player in players if other_player != self
        ]
        question = "Which player do you want to vote to execute?"
        choices = [
            PromptChoice(index=i, name=player.name)
            for i, player in enumerate(other_players)
        ]

        vote = await self.get_choice(question, choices)
        return other_players[vote[0]]

    async def get_choice(
        self,
        prompt: str,
        choices: List[PromptChoice],
        choose_multiple=False,
        min_choices=1,
        max_choices=None,
    ) -> List[int]:
        prompt_message = self.make_choice_prompt(
            prompt=prompt,
            choices=choices,
            choose_multiple=choose_multiple,
            min_choices=min_choices,
            max_choices=max_choices,
        )
        response = await self.prompt_with(prompt_message, should_think=True)

        valid_choices = [choice.index for choice in choices]
        try:
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
            selected_choices = [num for num in numbers if num in valid_choices]

            if len(selected_choices) < min_choices or (
                max_choices and len(selected_choices) > max_choices
            ):
                raise ValueError("Invalid number of choices")

            return selected_choices
        except (ValueError, AttributeError) as e:
            logger.warning(e)
            # If no valid choice was made, pick random valid choices
            random_choice_numbers = random.sample(valid_choices, min_choices)
            random_choice_names = [
                choice[1] for choice in choices if choice[0] in random_choice_numbers
            ]
            await self.observe(
                BaseMessage(
                    type="Invalid input",
                    message=f"Invalid choice. Randomly chose {random_choice_names}",
                )
            )
            return random_choice_numbers

    def make_choice_prompt(
        self,
        prompt,
        choices: List[PromptChoice],
        choose_multiple,
        min_choices,
        max_choices,
    ):
        return PromptMessage(
            message=prompt,
            choices=choices,
            multiple=choose_multiple,
            min_choices=min_choices,
            max_choices=max_choices,
        )

    async def prompt_with(
        self, prompt: Union[str, PromptMessage], should_think=False
    ) -> str:
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

    async def speak(self, chat=False) -> str:
        prompt = "What would you like to say to the other players?"
        if chat:
            prompt += " This is post game chat."
        message = await self.prompt_with(prompt)
        return f"{message}"

    async def observe(self, event: BaseEvent):
        await super().observe(event)
        await self.print(event)

    async def print(self, event: BaseEvent):
        raise NotImplementedError

    async def prompt_with(
        self, prompt: Union[str, PromptMessage], should_think=False, params: dict = None
    ) -> str:
        raise NotImplementedError


class LocalHumanPlayer(HumanPlayer):
    async def prompt_with(
        self, prompt: Union[str, PromptMessage], should_think=False, params: dict = None
    ) -> str:
        if isinstance(prompt, PromptMessage):
            prompt_text = prompt.text
        else:
            prompt_text = prompt
        return await ainput(prompt_text)

    async def print(self, event: BaseEvent):
        if isinstance(event, BaseMessage):
            print(event.message)


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
        self, prompt: Union[str, PromptMessage], should_think=False, params: dict = None
    ) -> str:
        if isinstance(prompt, PromptMessage):
            prompt_text = prompt.text
            prompt_event = prompt
        else:
            prompt_text = prompt
            prompt_event = PromptMessage(message=prompt, username="System")

        logger.info(f"prompting {self.login.name} with {prompt_text[:20]}")
        return await websocket_manager.get_input(self.user_id, prompt_event)

    async def print(self, event: BaseEvent):
        logger.info(f"informing {self.login.name} with {event}")
        await websocket_manager.send_personal_message(event, self.user_id)

    def update_activity(self):
        self.last_activity = time.time()

    async def wait_for_ready(self):
        ready_prompt = PromptMessage(
            message="",
            choices=[PromptChoice(index=1, name="Start Game")],
        )
        await websocket_manager.get_input(self.user_id, ready_prompt, timeout=None)


def get_rules(roles: List[Role]) -> str:
    rules = "Rules:\n"
    rules += "You and each other player, has a secret role with an ability and objective. Most players need to identify and vote for a werewolf, while werewolves need to look like innocents."
    rules += "You see your role at the start of the game, but that role may be changed during the night phase. Three more unused roles are in the center.\n\n"
    rules += (
        "First there is a night phase where certain roles will act.\n"
        "Players may have their roles changed during the night, but they'll perform their original role's action in the night anyway. Usually a player has no way of knowing if their role changed.\n"
        "Roles activate in the order they're described below.\n\n"
    )

    seen_roles = set()
    for role in sorted(roles, key=lambda r: r.wake_order):
        if role not in seen_roles:
            seen_roles.add(role)
            rules += role.get_rules() + "\n\n"

    rules += "\nDuring the day, each player will vote for someone to execute. The players with the most votes (all on a tie) will be executed. Werewolves win if no werewolf is executed. Other roles win if a werewolf to be executed unless their rules say otherwise.\n"
    rules += (
        "Then the game is over and winners are determined. There is only one round.\n"
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

    async def speak(self, chat=False) -> str:
        prompt = ""
        if self.personality:
            prompt += f"\nYour personality is: {self.personality} Don't over do it, focus on the game.\n"

        if chat:
            prompt += "What would you like to say to the other players? This is just post game chat, there's no more need to hide or be deceptive."
            response = await self.prompt_with(
                prompt, should_think=False, should_rules_check=False
            )
        else:
            prompt += "What would you like to say to the other players? After thinking, enter your message between curly brackets like {This is my message.} Focus on showing reasoning to be convincing, usually 1-3 sentences. Be intentional about what you share - don't self incriminate. Try to *accomplish* something with your message, don't pass or be scared of risk. Players expect you to tell your role and observations, and you will look suspicious if you don't. If you say you're a role, they'll expect you to have the information that role would have. If you say you have information, they will expect your role to back it up. Don't say you have a hunch or feeling, make solid claims."
            response = await self.prompt_with(
                prompt, should_think=True, should_rules_check=True
            )
        message_to_broadcast = response.split("{")[-1]
        message_to_broadcast = message_to_broadcast.replace("}", "")
        return f"{message_to_broadcast}"

    async def prompt_with(
        self,
        prompt: Union[str, PromptMessage],
        should_think=False,
        should_rules_check=False,
    ) -> str:
        litellm_prompt = Prompt().add_message(
            f"You're playing a social deduction game. Your name is {self.name}",
            role="system",
        )

        rules = get_rules(self.game.state.role_pool)

        litellm_prompt.add_message(rules, role="system")

        for observation in self.observations:
            if (
                isinstance(observation, SpeechMessage)
                and observation.username == self.name
            ):
                # skip messages from self
                continue

            if isinstance(observation, BaseMessage):
                litellm_prompt = litellm_prompt.add_message(
                    observation.ai_friendly_message, role="system"
                )
            else:
                litellm_prompt = litellm_prompt.add_message(
                    str(observation.model_dump()), role="system"
                )

        if isinstance(prompt, PromptMessage):
            prompt_text = prompt.text
        else:
            prompt_text = prompt

        if should_think:
            prompt_text = self.think_prompt + prompt_text

        litellm_prompt = litellm_prompt.add_message(prompt_text, role="system")
        response = await self.prompt_model(litellm_prompt)

        await self.observe(
            BaseMessage(
                type="my_action",
                message=f"I was asked: {prompt_text}\n\n I responded: {response}\n\n\n",
            )
        )

        if should_rules_check:
            error_found = await self.check_rules(response)
            if error_found:
                new_prompt = (
                    "\n\nDue to the previous possible rules error, you are given a chance to rethink your action. You can make the same decision if you believe you were correct."
                    + prompt_text
                )
                response = await self.prompt_with(
                    prompt=new_prompt, should_think=True, should_rules_check=False
                )

        return response

    async def check_rules(self, message: str) -> bool:
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

        error_found = "no errors found" in response.lower()

        if error_found:
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
        return error_found

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

    def make_choice_prompt(
        self,
        prompt,
        choices: List[PromptChoice],
        choose_multiple,
        min_choices,
        max_choices,
    ):
        choice_prompt = prompt + "\n"

        if choose_multiple:
            choice_prompt += "\nYour final answer must take the form {choice_numbers, choice names}, eg {1 3, Bob Clyde}."
        else:
            choice_prompt += "\nYour final answer must take the form {choice_number, choice name}, eg {1, Bob}."

        return PromptMessage(
            message=choice_prompt,
            choices=choices,
            multiple=choose_multiple,
            min_choices=min_choices,
            max_choices=max_choices,
        )


async def everyone_observe(players: List[Player], event: BaseEvent):
    await asyncio.gather(*[player.observe(event) for player in players])
