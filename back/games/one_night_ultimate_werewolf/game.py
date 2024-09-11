import asyncio
import random
from typing import List

from ai_models import get_random_model
from model_performance import performance_tracker
from ai_personalities import PERSONALITIES
from player import Player, HumanPlayer, AIPlayer, WebHumanPlayer
from onuw_roles import get_roles_in_game, assign_roles

from base_game import Game

class OneNightWerewolf(Game):
    def __init__(self, num_players: int, has_human: bool = False, websocket=None):
        super().__init__(num_players, has_human)
        self.websocket = websocket

    async def setup_game(self) -> None:
        # Create players
        if self.has_human:
            num_ai = self.num_players - 1
            if self.websocket:
                self.players.append(WebHumanPlayer(game=self, name="Human", websocket=self.websocket))
            else:
                self.players.append(HumanPlayer(game=self, name="Human"))
        else:
            num_ai = self.num_players

        ai_pool = PERSONALITIES.copy()
        for i in range(num_ai):
            name = random.choice(list(ai_pool.keys()))
            personality = ai_pool[name]
            del ai_pool[name]

            model = get_random_model()

            player = AIPlayer(game=self, name=name, model=model, personality=personality)

            self.players.append(player)

        random.shuffle(self.players)

        for player in self.players:
            await player.observe(f"The players in this game are: {', '.join([p.name for p in self.players])}.")

        # Assign roles
        roles_in_game = get_roles_in_game(len(self.players))
        center_cards = assign_roles(self.players, roles_in_game=roles_in_game)
        self.game_state.role_pool = roles_in_game
        for player in self.players:
            await player.observe(f"The full role pool in this game are: {', '.join([role.name for role in roles_in_game])}. Remember that 3 of them are in the center, not owned by other players.")
        self.game_state.add_center_cards(center_cards)
        self.game_state.set_players(self.players)

        for player in self.players:
            await player.observe(f"Your role's strategy: {player.role.get_strategy(self.game_state)}\n")

    async def play_night_phase(self) -> None:
        print("\n--- Night Phase ---")
        if self.websocket:
            await self.websocket.send_json({"type": "phase", "phase": "night"})
        night_roles = [role for role in self.game_state.role_pool if role.wake_order < 100]
        night_roles.sort(key=lambda role: role.wake_order)
        seen_roles = []
        for role in night_roles:
            if role not in seen_roles:
                seen_roles.append(role)
                for player in [
                    player for player in self.players if player.original_role == role
                ]:
                    action = await player.night_action(self.game_state)
                    if action:
                        self.game_state.record_night_action(player, action)

    async def handle_conversations(self):
        num_rounds = 3  # You can adjust this
        for round_i in range(num_rounds):
            conversation_round_message = f"\nConversation Round {round_i + 1} / {num_rounds}"
            if round_i + 1 == num_rounds:
                conversation_round_message += " (FINAL CHANCE TO TALK)"
            print(conversation_round_message)
            for player in self.players:
                await player.observe(conversation_round_message)

            for player in self.players:
                message = await player.speak()
                for listening_player in self.players:
                    await listening_player.observe(message)
                if self.websocket:
                    await self.websocket.send_json({"type": "message", "player": player.name, "message": message})

    async def play_day_phase(self) -> None:
        print("\n--- Day Phase ---")
        if self.websocket:
            await self.websocket.send_json({"type": "phase", "phase": "day"})
        await self.handle_conversations()

    async def voting_phase(self) -> List[Player]:
        print("\n--- Voting Phase ---")
        if self.websocket:
            await self.websocket.send_json({"type": "phase", "phase": "voting"})

        votes = {}
        for player in self.players:
            voted_player = await player.vote([p for p in self.players if p != player])
            votes[player] = voted_player

        print("Votes:")
        for player, voted_player in votes.items():
            print(f"{player.name} voted for {voted_player.name}")
            if self.websocket:
                await self.websocket.send_json({"type": "vote", "voter": player.name, "voted": voted_player.name})

        # Count votes
        vote_count = {}
        for voted_player in votes.values():
            vote_count[voted_player] = vote_count.get(voted_player, 0) + 1

        # Find player(s) with the most votes
        max_votes = max(vote_count.values())
        executed_players = [p for p, v in vote_count.items() if v == max_votes]

        for executed_player in executed_players:
            print(f"\n{executed_player.name} has been executed!")
            if self.websocket:
                await self.websocket.send_json({"type": "executed", "player": executed_player.name})

        return executed_players

    def check_win_condition(self, executed_players: List[Player]) -> None:
        werewolves_exist = any([p for p in self.players if p.role.name == "Werewolf"])
        
        winners = [p for p in self.players if p.role.did_win(p, executed_players, werewolves_exist)]

        print("\nWinners:")
        for player in winners:
            print(f"{player.name} ({player.role.name})")
        
        print("\nFinal Roles:")
        for player in self.players:
            print(f"{player.name}: {player.role.name}")

        for player in self.players:
            if isinstance(player, AIPlayer):
                did_win = player in winners
                performance_tracker.update_performance(player, did_win=did_win)

        performance_tracker.save_performance_data()

    async def play_game(self) -> None:
        await self.setup_game()

        # self.think()
        await self.play_night_phase()

        # self.think()
        await self.play_day_phase()

        # self.think()
        executed_players = await self.voting_phase()
        self.check_win_condition(executed_players)

        total_cost = 0
        for player in self.players:
            if isinstance(player, AIPlayer):
                total_cost += player.total_cost
        print(f"Total cost: {total_cost:.2f} USD")
        print("\n--- Game Over ---")
        if self.websocket:
            await self.websocket.send_json({"type": "game_over", "total_cost": total_cost})

if __name__ == "__main__":
    game = OneNightWerewolf(num_players=5, has_human=True)

    asyncio.run(game.play_game())
