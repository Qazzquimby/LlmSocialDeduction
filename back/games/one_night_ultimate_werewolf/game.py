import asyncio
import random
from typing import List

from ai_models import get_random_model
from model_performance import performance_tracker
from ai_personalities import PERSONALITIES
from player import Player, AIPlayer, WebHumanPlayer, LocalHumanPlayer, everyone_observe
from .onuw_roles import get_roles_in_game, assign_roles

from base_game import Game


class OneNightWerewolf(Game):
    def __init__(self, num_players: int, has_human: bool = False, user_id: str = None):
        super().__init__(num_players, has_human)
        self.user_id = user_id

    async def setup_game(self) -> None:
        if self.has_human:
            num_ai = self.num_players - 1
            if self.user_id:
                self.players.append(
                    WebHumanPlayer(game=self, name="Human", user_id=self.user_id)
                )
            else:
                self.players.append(LocalHumanPlayer(game=self, name="Human"))
        else:
            num_ai = self.num_players

        ai_pool = PERSONALITIES.copy()
        for i in range(num_ai):
            name = random.choice(list(ai_pool.keys()))
            personality = ai_pool[name]
            del ai_pool[name]

            model = get_random_model()
            player = AIPlayer(
                game=self, name=name, model=model, personality=personality
            )
            self.players.append(player)

        random.shuffle(self.players)

        await everyone_observe(
            self.players,
            f"The players in this game are: {', '.join([p.name for p in self.players])}.",
        )

        # Assign roles
        roles_in_game = get_roles_in_game(len(self.players))
        center_cards = await assign_roles(self.players, roles_in_game=roles_in_game)
        self.game_state.role_pool = roles_in_game
        await everyone_observe(
            self.players,
            f"The full role pool in this game are: {', '.join([role.name for role in roles_in_game])}. Remember that 3 of them are in the center, not owned by other players.",
        )
        self.game_state.add_center_cards(center_cards)
        self.game_state.set_players(self.players)

        for player in self.players:
            await player.observe(
                f"Your role's strategy: {player.role.get_strategy(self.game_state)}\n"
            )

    async def play_night_phase(self) -> None:
        await everyone_observe(
            self.players,
            "Night phase begins.",
            observation_type="phase",
            params={"phase": "night"},
        )

        night_roles = sorted(
            [role for role in self.game_state.role_pool if role.wake_order < 100],
            key=lambda r: r.wake_order,
        )
        night_roles = list(dict.fromkeys(night_roles))  # ordered dedup
        for role in night_roles:
            for player in [p for p in self.players if p.original_role == role]:
                action = await player.night_action(self.game_state)
                if action:
                    self.game_state.record_night_action(player, action)

    async def play_day_phase(self) -> None:
        await everyone_observe(
            self.players,
            "Day phase begins",
            observation_type="phase",
            params={"phase": "day"},
        )

        num_rounds = 3
        for round_i in range(num_rounds):
            conversation_round_message = (
                f"\nConversation Round {round_i + 1} / {num_rounds}"
            )
            if round_i + 1 == num_rounds:
                conversation_round_message += " (FINAL CHANCE TO TALK)"

            await everyone_observe(self.players, conversation_round_message)

            for speaker in self.players:
                from app import notify_next_speaker

                await notify_next_speaker(self.id, speaker.name)
                message = await speaker.speak()
                await everyone_observe(
                    self.players,
                    message,
                    observation_type="speech",
                    params={"username": speaker.name},
                )

    async def voting_phase(self) -> List[Player]:
        await everyone_observe(
            self.players,
            "Beginning of voting phase",
            observation_type="phase",
            params={"phase": "voting"},
        )

        votes = {}
        for player in self.players:
            voted_player = await player.vote([p for p in self.players if p != player])
            votes[player] = voted_player

        for player, voted_player in votes.items():
            print(f"{player.name} voted for {voted_player.name}")

        vote_count = {}
        for voted_player in votes.values():
            vote_count[voted_player] = vote_count.get(voted_player, 0) + 1

        max_votes = max(vote_count.values())
        executed_players = [p for p, v in vote_count.items() if v == max_votes]

        for executed_player in executed_players:
            await everyone_observe(
                self.players, f"\n{executed_player.name} has been executed!"
            )

        return executed_players

    async def check_win_condition(self, executed_players: List[Player]) -> None:
        werewolves_exist = any(p for p in self.players if p.role.name == "Werewolf")
        winners = [
            p
            for p in self.players
            if p.role.did_win(p, executed_players, werewolves_exist)
        ]

        for winner in winners:
            await everyone_observe(self.players, f"{winner} wins!")

        for player in self.players:
            await everyone_observe(
                self.players, f"{player.name} was {player.role.name}."
            )

        for player in self.players:
            if isinstance(player, AIPlayer):
                performance_tracker.update_performance(
                    player, did_win=player in winners
                )
        performance_tracker.save_performance_data()

    async def play_game(self) -> None:
        await self.setup_game()
        await self.play_night_phase()
        await self.play_day_phase()
        executed_players = await self.voting_phase()
        await self.check_win_condition(executed_players)

        total_cost = 0
        for player in self.players:
            if isinstance(player, AIPlayer):
                total_cost += player.total_cost
        print(f"Total cost: {total_cost:.2f} USD")
        print("\n--- Game Over ---")


if __name__ == "__main__":
    game = OneNightWerewolf(num_players=5, has_human=True)
    asyncio.run(game.play_game())
