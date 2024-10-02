from loguru import logger

import asyncio
import random
from typing import List
import time

from ai_models import get_random_model
from games.one_night_ultimate_werewolf.onuw_roles import get_roles_in_game, assign_roles
from message_types import (
    ObservationMessage,
    GameStartedMessage,
    PhaseMessage,
    SpeechMessage,
    PlayerActionMessage,
    NextSpeakerMessage,
    GameEndedMessage,
)
from model_performance import performance_tracker
from ai_personalities import PERSONALITIES
from player import Player, AIPlayer, WebHumanPlayer, LocalHumanPlayer, everyone_observe
from message_types import BaseMessage
from websocket_management import UserLogin

from base_game import Game


class OneNightWerewolf(Game):
    def __init__(
        self, num_players: int, has_human: bool = False, login: UserLogin = None
    ):
        super().__init__(num_players, has_human)
        self.login = login
        self.current_phase = "setup"
        self.current_action = None
        self.last_action_time = time.time()

    async def setup_game(self) -> None:
        logger.info("Setting up game")
        if self.has_human:
            num_ai = self.num_players - 1
            if self.login:
                web_human_player = WebHumanPlayer(
                    game=self,
                    login=self.login,
                )
                self.state.add_player(web_human_player)
            else:
                self.state.add_player(LocalHumanPlayer(game=self, name="Human"))
        else:
            num_ai = self.num_players

        ai_pool = PERSONALITIES.copy()
        for i in range(num_ai):
            name = random.choice(list(ai_pool.keys()))
            personality = ai_pool[name]
            del ai_pool[name]

            model = get_random_model()
            player = AIPlayer(
                game=self,
                name=name,
                model=model,
                personality=personality,
                api_key=self.get_key(),
            )
            self.state.add_player(player)

        random.shuffle(self.state.players)

        await everyone_observe(
            self.state.players,
            GameStartedMessage(
                message=f"The players in this game are: {', '.join([p.name for p in self.state.players])}.",
                players=[p.name for p in self.state.players],
            ),
        )

        # Assign roles
        roles_in_game = get_roles_in_game(len(self.state.players))
        center_cards = await assign_roles(
            self.state.players, roles_in_game=roles_in_game
        )
        self.state.role_pool = roles_in_game
        await everyone_observe(
            self.state.players,
            ObservationMessage(
                message=f"The full role pool in this game are: {', '.join([role.name for role in roles_in_game])}. Remember that 3 of them are in the center, not owned by other players."
            ),
        )
        self.state.add_center_cards(center_cards)

        for player in self.state.players:
            await player.observe(
                ObservationMessage(
                    message=f"Your role's strategy: {player.role.get_strategy(self.state)}\n"
                )
            )

    async def play_night_phase(self) -> None:
        logger.info("Starting night phase")
        await everyone_observe(
            self.state.players,
            PhaseMessage(message="Night phase begins.", phase="night"),
        )

        night_roles = sorted(
            [role for role in self.state.role_pool if role.wake_order < 100],
            key=lambda r: r.wake_order,
        )
        night_roles = list(dict.fromkeys(night_roles))  # ordered dedup
        for role in night_roles:
            for player in [p for p in self.state.players if p.original_role == role]:
                action = await player.night_action(self.state)
                if action:
                    self.state.record_night_action(player, action)

    async def play_day_phase(self) -> None:
        await everyone_observe(
            self.state.players,
            PhaseMessage(message="Day phase begins", phase="day"),
        )

        num_rounds = 3
        for round_i in range(num_rounds):
            conversation_round_message = (
                f"Conversation Round {round_i + 1} / {num_rounds}"
            )
            if round_i + 1 == num_rounds:
                conversation_round_message += " (FINAL CHANCE TO TALK)"

            await everyone_observe(
                self.state.players,
                ObservationMessage(message=conversation_round_message),
            )

            for speaker in self.state.players:
                await everyone_observe(
                    [p for p in self.state.players if isinstance(p, WebHumanPlayer)],
                    NextSpeakerMessage(player=speaker.name),
                )
                message = await speaker.speak()
                await everyone_observe(
                    self.state.players,
                    SpeechMessage(message=message, username=speaker.name),
                )

    async def voting_phase(self) -> List[Player]:
        await everyone_observe(
            self.state.players,
            PhaseMessage(message="Beginning of voting phase", phase="voting"),
        )

        votes = {}
        for player in self.state.players:
            voted_player = await player.vote(
                [p for p in self.state.players if p != player]
            )
            votes[player] = voted_player

        for player, voted_player in votes.items():
            await everyone_observe(
                self.state.players,
                BaseMessage(
                    type="player_voted",
                    message=f"{player.name} voted for {voted_player.name}",
                ),
            )

        vote_count = {}
        for voted_player in votes.values():
            vote_count[voted_player] = vote_count.get(voted_player, 0) + 1

        max_votes = max(vote_count.values())
        executed_players = [p for p, v in vote_count.items() if v == max_votes]

        for executed_player in executed_players:
            await everyone_observe(
                self.state.players,
                PlayerActionMessage(
                    message=f"\n{executed_player.name} has been executed!",
                    player=executed_player.name,
                    action="executed",
                ),
            )

        return executed_players

    async def check_win_condition(self, executed_players: List[Player]) -> None:
        werewolves_exist = any(
            p for p in self.state.players if p.role.name == "Werewolf"
        )
        winners = [
            p
            for p in self.state.players
            if p.role.did_win(p, executed_players, werewolves_exist)
        ]

        for winner in winners:
            await everyone_observe(
                self.state.players,
                PlayerActionMessage(
                    message=f"{winner} wins!", player=winner.name, action="win"
                ),
            )

        for player in self.state.players:
            await everyone_observe(
                self.state.players,
                PlayerActionMessage(
                    message=f"{player.name} started as {player.original_role.name} and ended as {player.role.name}.",
                    player=player.name,
                    action="reveal_role",
                ),
            )

        for player in self.state.players:
            if isinstance(player, AIPlayer):
                performance_tracker.update_performance(
                    player, did_win=player in winners
                )
        performance_tracker.save_performance_data()

    async def play_game(self) -> None:
        try:
            await self.setup_game()
            await self.play_night_phase()
            await self.play_day_phase()
            executed_players = await self.voting_phase()
            await self.check_win_condition(executed_players)

            total_cost = 0
            for player in self.state.players:
                if isinstance(player, AIPlayer):
                    total_cost += player.total_cost
            print(f"Total cost: {total_cost:.2f} USD")
            print("\n--- Game Over ---")
        finally:
            logger.info(f"Game {self.id} ended")
            self.game_over = True
            await everyone_observe(
                players=self.state.players,
                event=GameEndedMessage(message="The game has ended."),
            )

    def get_key(self):
        """Returns the key of a random player. Intended to fairly distribute costs to present players."""
        web_players = [
            player
            for player in self.state.players
            if isinstance(player, WebHumanPlayer)
        ]
        if web_players:
            web_player = random.choice(web_players)
            return web_player.login.api_key
        return None


if __name__ == "__main__":
    from app import GameManager

    game_manager = GameManager(OneNightWerewolf(num_players=5, has_human=True))
    game_manager.game.game_manager = game_manager  # todo, gross.
    asyncio.run(game_manager.game.play_game())
