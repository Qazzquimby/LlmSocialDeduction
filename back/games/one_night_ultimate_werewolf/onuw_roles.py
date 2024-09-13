import random
from typing import List, TYPE_CHECKING, Optional

from roles import Role, RoleInteraction

if TYPE_CHECKING:
    from game_state import GameState
    from player import Player


class ONUWRole(Role):
    def __init__(self, name, wake_order=999.0):
        super().__init__(name)
        self.wake_order = wake_order


class Werewolf(ONUWRole):
    def __init__(self):
        super().__init__("Werewolf", wake_order=2)

    async def night_action(self, player: "Player", game_state: "GameState") -> str:
        other_werewolves = [
            p
            for p in game_state.players
            if p != player and isinstance(p.role, Werewolf)
        ]
        if other_werewolves:
            other_werewolves_names = ", ".join(w.name for w in other_werewolves)
            return f"You see that {other_werewolves_names} is/are also Werewolf/Werewolves."
        else:
            random_center_card = random.choice(game_state.center_cards)
            return f"You see there is no other Werewolf. You see a {random_center_card.name} in the center."

    def get_rules(self) -> str:
        return "Werewolves will see the identities of other werewolves during the night phase. If there are no other werewolves, they see a random center card. They win if no Werewolf is executed."

    def did_win(
        self, player: "Player", executed_players: List["Player"], werewolves_exist: bool
    ) -> bool:
        return not any(
            [isinstance(p.role, Werewolf) for p in executed_players]
        ) and not any([isinstance(p.role, Tanner) for p in executed_players])

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "Generally, it is best to claim Village roles that gain no or little information, like Troublemaker",
            "You should be spreading misinformation whenever possible if you don't think you'll be contradicted. Whenever you have real information, like knowing a center card, don't share it unless someone else will back it up and make you look trustworthy.",
            "Werewolves need to care more about causing confusion than figuring out other's roles.",
            "If you're a solo werewolf you learn one of the center roles, which is probably safe to claim to be. ",
        ]

    def get_interaction_strategy_lines(self) -> List[RoleInteraction]:
        return [
            RoleInteraction(
                Tanner(),
                "You can also try to claim Werewolf, as no Werewolf would reveal themselves. This will likely make you called a Tanner, causing nobody to vote for you. Note that you lose if a Tanner is executed.",
            ),
            RoleInteraction(
                Robber(),
                "You could claim Robber and say you robbed someone right as they claim",
            ),
            # RoleInteraction(Mason(), "If there is another Werewolf, both of you could claim to be Masons that saw each other, this will almost certainly be contradicted by someone so you need to be convincing"),
            RoleInteraction(
                Seer(),
                "If you are a solo Werewolf, you can claim to be a Seer that saw the card you saw in the center and a Werewolf, since there is actually a Werewolf card in the center",
            ),
            # RoleInteraction(Drunk(), "If there are a lot of suspicious people, you can claim to be a Drunk as you likely saw a Village Team card, however if the village thinks there might be no Werewolves, they will likely kill you since you likely are a Werewolf now"),
            RoleInteraction(
                Troublemaker(),
                "A risky yet effective strategy is to claim Troublemaker and claim to have swapped a fellow Werewolf with a non-Werewolf and have the fellow Werewolf out their role and claim that the non-Werewolf in now a Werewolf",
            ),
        ]


class Villager(ONUWRole):
    def __init__(self):
        super().__init__("Villager")

    def get_rules(self) -> str:
        return "The Villager has no special abilities."

    def did_win(
        self, player: "Player", executed_players: List["Player"], werewolves_exist: bool
    ) -> bool:
        return (
            any(isinstance(p.role, Werewolf) for p in executed_players)
            or not werewolves_exist
        )

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "The main strategy for a villager player involves manipulating one of the werewolves into claiming Villager, thus narrowing the number of suspects for team village.",
            "Villager is a really attractive claim for a Werewolf as you're not given any secret information. Consider not claiming to be Villager initially as it is a suspicious claim.",
            "Make false claims. This leaves fewer roles open for werewolves to claim safely. Werewolves don't want to narrow it down to two suspects.",
            "Once you've located a werewolf, if you're also suspected of being a werewolf, call for a split vote between you and the werewolf, this is advantageous for team village, and the werewolf can't fight it without looking suspicious. Make sure to ask for all suspected werewolves to vote for you, so the werewolves can't ruin the vote.",
        ]


class Seer(ONUWRole):
    def __init__(self):
        super().__init__("Seer", wake_order=5)

    async def night_action(self, player: "Player", game_state: "GameState") -> str:
        players = game_state.players
        options = "0: Look at two center cards\n" + "\n".join(
            [
                f"{i}: Look at {p.name}'s card"
                for i, p in enumerate(players, 1)
                if p != player
            ]
        )
        prompt = f"{player.name}, choose a number:\n{options}\nEnter your choice:"
        choice = await player.get_choice(prompt)

        if len(choice) >= 1 and choice[0] == 0:
            cards = game_state.center_cards[:2]
            return (
                f"You see the following center cards: {cards[0].name}, {cards[1].name}"
            )
        elif len(choice) >= 1 and 1 <= choice[0] <= len(players):
            target = players[choice[0] - 1]
            return f"You see that {target.name}'s role is: {target.role.name}"
        else:
            return "Invalid choice. You lose your night action."

    def get_rules(self) -> str:
        return "During the night, the seer can either see the role of another player, or see *two* of the unused center cards."

    def did_win(
        self, player: "Player", executed_players: List["Player"], werewolves_exist: bool
    ) -> bool:
        return (
            any(isinstance(p.role, Werewolf) for p in executed_players)
            or not werewolves_exist
        )

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "The Seer should almost always look at 2 center cards, not only do they gain more information this way, it's very easy to refute the Seer's claim about a player's role.",
            "The Seer should debate on whether to reveal early or after someone claims a role she saw in the center but should never reveal what she saw in the center because they can wait too see if someone claims the role they saw",
            "Claiming early will make you sound more trustworthy, and may make a solo Werewolf more wary of claiming the role they saw in the center, even if the Seer did not see the card messing up their claim",
            "Waiting to claim until someone claims a role you saw in the center can make it more likely for you to be able to counter them, and if you wait even longer for someone to back up their claim means you can find who the Werewolves are easily, but you might be more suspicious for not claiming earlier",
        ]

    def get_interaction_strategy_lines(self) -> List[RoleInteraction]:
        return [
            # RoleInteraction(MysticWolf(), "If you view a player's card, If a Mystic Wolf is in play, you will be extremely suspicious for essentially preforming the Mystic Wolf's action and will likely be lynched."),
            # RoleInteraction(Drunk(), "When the Drunk or Witch is in play, pay attention to which cards you viewed"),
            # RoleInteraction(Witch(), "When the Drunk or Witch is in play, pay attention to which cards you viewed"),
        ]


class Robber(ONUWRole):
    def __init__(self):
        super().__init__("Robber", wake_order=6)

    async def night_action(self, player: "Player", game_state: "GameState") -> str:
        players = game_state.players
        options = "\n".join(
            [f"{i}: Rob {p.name}" for i, p in enumerate(players, 1) if p != player]
        )
        prompt = (
            f"{player.name}, choose a player to rob:\n{options}\nEnter your choice:"
        )
        choice = await player.get_choice(prompt)

        if len(choice) >= 1 and 1 <= choice[0] <= len(players):
            target = players[choice[0] - 1]
            player.role, target.role = target.role, player.role
            return f"You swapped roles with {target.name}. Your new role is: {player.role.name}"
        else:
            return "Invalid choice. You lose your night action."

    def get_rules(self) -> str:
        return "During the night, the Robber may swap their card with another player's card and see what their new card is. The other player won't know their card changed."

    def did_win(
        self, player: "Player", executed_players: List["Player"], werewolves_exist: bool
    ) -> bool:
        return (
            any(isinstance(p.role, Werewolf) for p in executed_players)
            or not werewolves_exist
        )

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "If the Robber steals a village card they can confirm them and back them up. Claim before they reveal to look more legitimate, though this may look like you're a werewolf giving another werewolf an alibi.",
            "They can also say they robbed someone but won't reveal until later so that the person you robbed can lie, as otherwise their role would be confirmed and they could not lie",
            "If you are now a Werewolf, say you robbed someone you didn't right after they claim as you now have an alibi that no one can really refute. Then, whoever the Werewolf you robbed is will still think they are a Werewolf and will act like a Werewolf so try and push them as much as possible and lead a victory to team Werewolf.",
        ]

    def get_interaction_strategy_lines(self) -> List[RoleInteraction]:
        return []


class Troublemaker(ONUWRole):
    def __init__(self):
        super().__init__("Troublemaker", wake_order=7)

    async def night_action(self, player: "Player", game_state: "GameState") -> str:
        players = game_state.players
        options = "\n".join(
            [f"{i}: {p.name}" for i, p in enumerate(players, 1) if p != player]
        )
        prompt = f"{player.name}, choose two players to swap roles:\n{options}\nEnter the choices numbers of both players separated by a space, like `2 3`. For example you might say your thoughts and then {{1 3, Tom and Ernie, Since this is the start of the game I'm choosing mostly at random.}}"
        choices = await player.get_choice(prompt)

        if (
            len(choices) == 2
            and 1 <= choices[0] <= len(players)
            and 1 <= choices[1] <= len(players)
            and choices[0] != choices[1]
        ):
            player1 = players[choices[0] - 1]
            player2 = players[choices[1] - 1]
            player1.role, player2.role = player2.role, player1.role
            return f"You swapped the roles of {player1.name} and {player2.name}."
        else:
            return "Invalid choice. You lose your night action."

    def get_rules(self) -> str:
        return "The Troublemaker may swap two other players' cards without seeing them during the night phase."

    def did_win(
        self, player: "Player", executed_players: List["Player"], werewolves_exist: bool
    ) -> bool:
        return (
            any(isinstance(p.role, Werewolf) for p in executed_players)
            or not werewolves_exist
        )

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "Troublemaker can lie about who they swapped which may cause a werewolf to out themselves, thinking they're now a villager.",
            "Since troublemaker gains no new information, it's very easy for a werewolf to pretend to be a troublemaker",
        ]

    def get_interaction_strategy_lines(self) -> List[RoleInteraction]:
        return []


class Tanner(ONUWRole):
    def __init__(self):
        super().__init__("Tanner")

    def get_rules(self) -> str:
        return "The Tanner wins if they are executed. They lose in all other scenarios. Werewolves lose if tanner is executed."

    def did_win(
        self, player: "Player", executed_players: List["Player"], werewolves_exist: bool
    ) -> bool:
        return player in executed_players

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "If you claim to have been a Werewolf, you will likely be called a Tanner as this is a very obvious play that no Werewolf would do (unless they want people to think they're a tanner).",
            "A Tanner can claim to be a Tanner, as it may make them look like a Werewolf trying to avoid being voted for. A good werewolf wouldn't be so direct early on though.",
            "In general, claiming something anyone else has claimed is a good strategy.",
            "Pretending to be any role that gains information, but not having any information to share, may make the town think you're a struggling werewolf.",
        ]

    def get_interaction_strategy_lines(self) -> List[RoleInteraction]:
        return [
            # RoleInteraction(Mason(), "Claiming Mason is suspicious so it might just get you killed, since if there is another Mason would see you and a solo Mason is suspicious."),
            RoleInteraction(
                Robber(),
                "Claiming to be a Robber who robbed someone suspicious will direct suspicions towards you.",
            ),
            # RoleInteraction(Drunk(), "A Strategy is to claim to be a Drunk if the Village thinks there might not be any Werewolves.")
            # RoleInteraction(Doppelganger(), "Claiming Doppelganger is a bit finicky, if you claim to have viewed a role that someone isn't, or performing the role incorrectly you might get killed, but this is almost too subtle."),
            # RoleInteraction(ParanormalInvestigator(), "Claiming Paranormal Investigator is a good idea since they are potentially a Werewolf now."),
        ]


class Insomniac(ONUWRole):
    def __init__(self):
        super().__init__("Insomniac", wake_order=9)

    def get_rules(self) -> str:
        return "At the end of the night phase, the Insomniac looks at their card to see if it has changed."

    def did_win(
        self, player: "Player", executed_players: List["Player"], werewolves_exist: bool
    ) -> bool:
        return (
            any(isinstance(p.role, Werewolf) for p in executed_players)
            or not werewolves_exist
        )

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "If you discover you're now a werewolf, when someone says they swapped you, you can claim you used to be the werewolf to put doubt on the person you swapped with."
        ]

    async def night_action(
        self, player: "Player", game_state: "GameState"
    ) -> Optional[str]:
        new_role = player.role.name
        if new_role == player.original_role.name:
            return "You are still the Insomniac."
        else:
            return f"You see that your role has changed to {new_role}."


class Thing(ONUWRole):
    def __init__(self):
        super().__init__("Thing", wake_order=4.2)

    def get_rules(self) -> str:
        return "During the night phase, the Thing taps a player next to them in turn order."

    def did_win(
        self, player: "Player", executed_players: List["Player"], werewolves_exist: bool
    ) -> bool:
        return (
            any(isinstance(p.role, Werewolf) for p in executed_players)
            or not werewolves_exist
        )

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "If a player confirms they were tapped it can back up you claim as a team village player.",
            "Werewolves may not want to confirm they were tapped to avoid backing you up.",
        ]

    async def night_action(
        self, player: "Player", game_state: "GameState"
    ) -> Optional[str]:
        my_index = game_state.players.index(player)
        previous_index = my_index - 1
        next_index = (my_index + 1) % len(game_state.players)
        adjacent_players = [
            game_state.players[previous_index],
            game_state.players[next_index],
        ]

        choices = await player.get_choice(
            "choose an adjacent player to tap: "
            + "\n".join([f"{i}: {p.name}" for i, p in enumerate(adjacent_players, 1)])
        )

        if len(choices) == 1 and 1 <= choices[0] <= len(adjacent_players):
            target = adjacent_players[choices[0] - 1]
            await target.observe(
                "An player before or after you in turn order is the Thing and tapped you."
            )
            return f"You tap {target.name}."
        else:
            return "Invalid choice. You lose your night action."


class Doppelganger(ONUWRole):
    def __init__(self):
        super().__init__("Doppelganger", wake_order=1)

    def get_rules(self) -> str:
        return "During the night phase, the Doppelganger looks at another player's card and becomes that card's role, immediately taking it's night action. Essentially there may be 1 more of any role."

    def did_win(
        self, player: "Player", executed_players: List["Player"], werewolves_exist: bool
    ) -> bool:
        print(
            "WARN: Doppelganger is checking for win condition, which is uncommon unless doppelganger was gained from the center."
        )
        return (
            any(isinstance(p.role, Werewolf) for p in executed_players)
            or not werewolves_exist
        )

    async def night_action(
        self, player: "Player", game_state: "GameState"
    ) -> Optional[str]:
        players = game_state.players
        options = "\n".join(
            [f"{i}: Copy {p.name}" for i, p in enumerate(players, 1) if p != player]
        )
        prompt = f"{player.name}, choose a player to copy their role:\n{options}\nEnter your choice:"
        choice = await player.get_choice(prompt)

        if len(choice) >= 1 and 1 <= choice[0] <= len(players):
            target = players[choice[0] - 1]
            action_text = f"You copied the role of {target.name}. Your new role is: {target.role.name}"

            player.role = target.role
            second_night_action_text = await player.role.night_action(
                player, game_state
            )
            if second_night_action_text:
                action_text += (
                    f"\nThen, as the {player.role.name}: " + second_night_action_text
                )
            return action_text
        else:
            return "Invalid choice. You lose your night action."

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "You must take on the strategy of whatever role you take.",
            "Note that if your role is swapped away, it will still be the role you copied, not 'Doppelganger'.",
        ]


def get_roles_in_game(num_players: int) -> List[Role]:
    global_role_pool = [Werewolf(), Werewolf()]

    village_roles = [
        # Seer(),
        Robber(),
        Troublemaker(),
        Tanner(),
        # Villager(), Villager(), Villager(),
        Insomniac(),
        Thing(),
        Doppelganger(),
    ]
    random.shuffle(village_roles)
    global_role_pool += village_roles

    role_pool_for_this_many_players = global_role_pool[: num_players + 3]
    return role_pool_for_this_many_players


async def assign_roles(
    players: List["Player"], roles_in_game: List[Role]
) -> List[Role]:
    roles = roles_in_game[:]
    random.shuffle(roles)

    for player, role in zip(players, roles[: len(players)]):
        await player.set_role(role)

    return roles[len(players) :]  # Return unused roles
