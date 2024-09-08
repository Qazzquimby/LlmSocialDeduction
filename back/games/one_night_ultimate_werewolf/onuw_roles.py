import random
from typing import List, TYPE_CHECKING

from roles import Role, RoleInteraction

if TYPE_CHECKING:
    from game_state import GameState
    from player import Player


class Werewolf(Role):
    def __init__(self):
        super().__init__("Werewolf")

    def night_action(self, player: "Player", game_state: "GameState") -> str:
        other_werewolves = [p for p in game_state.players if
                            p != player and isinstance(p.role, Werewolf)]
        if other_werewolves:
            other_werewolves_names = ", ".join(
                w.name for w in other_werewolves)
            return f"You see that {other_werewolves_names} is/are also Werewolf/Werewolves."
        else:
            random_center_card = random.choice(game_state.center_cards)
            return f"You see there is no other Werewolf. You see a {random_center_card.name} in the center."

    def get_rules(self) -> str:
        return "Werewolves will see the identities of other werewolves during the night phase. If there are no other wereolves, they see a random center card. They win if no Werewolf is executed."

    def did_win(self, player: 'Player', executed_players: List['Player'],
                werewolves_exist: bool) -> bool:
        return (
                not any([
                    isinstance(p.role, Werewolf) for p in executed_players
                ])
                and
                not any([
                    isinstance(p.role, Tanner) for p in executed_players
                ])
        )

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "Generally, it is best to claim Village roles that gain no or little information, like Troublemaker"
        ]

    def get_interaction_strategy_lines(self) -> List[RoleInteraction]:
        return [
            RoleInteraction(Tanner(),
                            "You can also try to claim Werewolf, as no Werewolf would reveal themselves. This will likely make you called a Tanner, causing nobody to vote for you."),
            RoleInteraction(Robber(),
                            "You could claim Robber and say you robbed someone right as they claim"),
            # RoleInteraction(Mason(), "If there is another Werewolf, both of you could claim to be Masons that saw each other, this will almost certainly be contradicted by someone so you need to be convincing"),
            RoleInteraction(Seer(),
                            "If you are a solo Werewolf, you can claim to be a Seer that saw the card you saw in the center and a Werewolf, since there is actually a Werewolf card in the center"),
            # RoleInteraction(Drunk(), "If there are a lot of suspicious people, you can claim to be a Drunk as you likely saw a Village Team card, however if the village thinks there might be no Werewolves, they will likely kill you since you likely are a Werewolf now"),
            RoleInteraction(Troublemaker(),
                            "A risky yet effective strategy is to claim Troublemaker and claim to have swapped a fellow Werewolf with a non-Werewolf and have the fellow Werewolf out their role and claim that the non-Werewolf in now a Werewolf"),
        ]


class Villager(Role):
    def __init__(self):
        super().__init__("Villager")

    def get_rules(self) -> str:
        return "The Villager has no special abilities."

    def did_win(self, player: 'Player', executed_players: List['Player'],
                werewolves_exist: bool) -> bool:
        return any(isinstance(p.role, Werewolf) for p in
                   executed_players) or not werewolves_exist

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "The main strategy for a villager player involves manipulating one of the werewolves into claiming Villager, thus narrowing the number of suspects for team village.",
            "Villager is a really attractive claim for a Werewolf or Dream Wolf as you're not given any secret information. Because of this you should never claim Villager initially, as it is a very suspicious claim.",
            "Make false claims. This leaves fewer roles open for werewolves to claim safely. Werewolves don't want to narrow it down to two suspects.",
            "Once you've located a werewolf, if you're also suspected of being a werewolf, call for a split vote between you and the werewolf, this is advantageous for team village, and the werewolf can't fight it without looking suspicious. Make sure to ask for all suspected werewolves to vote for you, so the werewolves can't ruin the vote.",
        ]


class Seer(Role):
    def __init__(self):
        super().__init__("Seer")

    def night_action(self, player: "Player", game_state: "GameState") -> str:
        players = game_state.players
        options = "0: Look at two center cards\n" + "\n".join(
            [f"{i}: Look at {p.name}'s card" for i, p in enumerate(players, 1) if
             p != player])
        prompt = f"{player.name}, choose a number:\n{options}\nEnter your choice:"
        choice = player.get_choice(prompt)

        if len(choice) >= 1 and choice[0] == 0:
            cards = game_state.center_cards[:2]
            return f"You see the following center cards: {cards[0].name}, {cards[1].name}"
        elif len(choice) >= 1 and 1 <= choice[0] <= len(players):
            target = players[choice[0] - 1]
            return f"You see that {target.name}'s role is: {target.role.name}"
        else:
            return "Invalid choice. You lose your night action."

    def get_rules(self) -> str:
        return "The Seer will see the identities of another player or two of the unused identities during the night phase."

    def did_win(self, player: 'Player', executed_players: List['Player'],
                werewolves_exist: bool) -> bool:
        return any(isinstance(p.role, Werewolf) for p in
                   executed_players) or not werewolves_exist

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "The Seer should almost always look at 2 center cards, not only do they gain more information this way, it's very easy to refute the Seer's claim about a player's role.",
            "The Seer should debate on whether to reveal early or after someone claims a role she saw in the center but should never reveal what she saw in the center because they can wait too see if someone claims the role they saw",
            "Claiming early will make you sound more trustworthy, and may make a solo Werewolf more wary of claiming the role they saw in the center, even if the Seer did not see the card messing up their claim",
            "Waiting to claim until someone claims a role you saw in the center can make it more likely for you to be able to counter them, and if you wait even longer for someone to back up their claim means you can find who the Werewolves are easily, but you might be more suspicious for not claiming earlier"
        ]

    def get_interaction_strategy_lines(self) -> List[RoleInteraction]:
        return [
            # RoleInteraction(MysticWolf(), "If you view a player's card, If a Mystic Wolf is in play, you will be extremely suspicious for essentially preforming the Mystic Wolf's action and will likely be lynched."),
            # RoleInteraction(Drunk(), "When the Drunk or Witch is in play, pay attention to which cards you viewed"),
            # RoleInteraction(Witch(), "When the Drunk or Witch is in play, pay attention to which cards you viewed"),
        ]


class Robber(Role):
    def __init__(self):
        super().__init__("Robber")

    def night_action(self, player: "Player", game_state: "GameState") -> str:
        players = game_state.players
        options = "\n".join(
            [f"{i}: Rob {p.name}" for i, p in enumerate(players, 1) if p != player])
        prompt = f"{player.name}, choose a player to rob:\n{options}\nEnter your choice:"
        choice = player.get_choice(prompt)

        if len(choice) >= 1 and 1 <= choice[0] <= len(players):
            target = players[choice[0] - 1]
            player.role, target.role = target.role, player.role
            return f"You swapped roles with {target.name}. Your new role is: {player.role.name}"
        else:
            return "Invalid choice. You lose your night action."

    def get_rules(self) -> str:
        return "The Robber may steal a player's card and see what it is during the night phase."

    def did_win(self, player: 'Player', executed_players: List['Player'],
                werewolves_exist: bool) -> bool:
        return any(isinstance(p.role, Werewolf) for p in
                   executed_players) or not werewolves_exist

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "If the Robber steals a village card they can confirm them and back them up. Claim before they reveal to look more legitimate, though this may look like you're a werewolf giving another werewolf an alibi.",
            "They can also say they robbed someone but won't reveal until later so that the person you robbed can lie, as otherwise their role would be confirmed and they could not lie",
            "If you are now a Werewolf, say you robbed someone you didn't right after they claim as you now have an alibi that no one can really refute. Then, whoever the Werewolf you robbed is will still think they are a Werewolf and will act like a Werewolf so try and push them as much as possible and lead a victory to team Werewolf.",
        ]

    def get_interaction_strategy_lines(self) -> List[RoleInteraction]:
        return [
        ]


class Troublemaker(Role):
    def __init__(self):
        super().__init__("Troublemaker")

    def night_action(self, player: "Player", game_state: "GameState") -> str:
        players = game_state.players
        options = "\n".join(
            [f"{i}: {p.name}" for i, p in enumerate(players, 1) if p != player])
        prompt = f"{player.name}, choose two players to swap roles:\n{options}\nEnter the choices numbers of both players separated by a space, like `2 3`:"
        choices = player.get_choice(prompt)

        if len(choices) == 2 and 1 <= choices[0] <= len(players) and 1 <= choices[
            1] <= len(players) and choices[0] != choices[1]:
            player1 = players[choices[0] - 1]
            player2 = players[choices[1] - 1]
            player1.role, player2.role = player2.role, player1.role
            return f"You swapped the roles of {player1.name} and {player2.name}."
        else:
            return "Invalid choice. You lose your night action."

    def get_rules(self) -> str:
        return "The Troublemaker may swap two other players' cards without seeing them during the night phase."

    def did_win(self, player: 'Player', executed_players: List['Player'],
                werewolves_exist: bool) -> bool:
        return any(isinstance(p.role, Werewolf) for p in
                   executed_players) or not werewolves_exist

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "Troublemaker can lie about who they swapped which may cause a werewolf to out themselves, thinking they're now a villager.",
            "Since troublemaker gains no new information, it's very easy for a werewolf to pretend to be a troublemaker",
        ]

    def get_interaction_strategy_lines(self) -> List[RoleInteraction]:
        return [
        ]


class Tanner(Role):
    def __init__(self):
        super().__init__("Tanner")

    def get_rules(self) -> str:
        return "The Tanner wins if they are executed. They lose in all other scenarios. Werewolves lose if tanner is executed."

    def did_win(self, player: 'Player', executed_players: List['Player'],
                werewolves_exist: bool) -> bool:
        return player in executed_players

    def get_general_strategy_lines(self) -> List[str]:
        return [
            "If you claim to have been a Werewolf, you will likely be called a Tanner as this is a very obvious play that no Werewolf would do (unless they want people to think they're a tanner).",
            "A Tanner can claim to be a Tanner, as no Tanner would reveal themselves, and they will likely be called as a Werewolf.",
            "In general, claiming something anyone else has claimed is a good strategy.",
            "Pretending to be any role that gains information, but not having any information to share, may make the town think you're a struggling werewolf."
        ]

    def get_interaction_strategy_lines(self) -> List[RoleInteraction]:
        return [
            # RoleInteraction(Mason(), "Claiming Mason is suspicious so it might just get you killed, since if there is another Mason would see you and a solo Mason is suspicious."),
            RoleInteraction(Robber(),
                            "Claiming to be a Robber who robbed someone suspicious will direct suspicions towards you."),
            # RoleInteraction(Drunk(), "A Strategy is to claim to be a Drunk if the Village thinks there might not be any Werewolves.")
            # RoleInteraction(Doppleganger(), "Claiming Doppelganger is a bit finicky, if you claim to have viewed a role that someone isn't, or performing the role incorrectly you might get killed, but this is almost too subtle."),
            # RoleInteraction(ParanormalInvestigator(), "Claiming Paranormal Investigator is a good idea since they are potentially a Werewolf now."),

        ]


def get_roles_in_game(num_players: int) -> List[Role]:
    global_role_pool = [
        Werewolf(), Werewolf(),
        Seer(), Robber(), Troublemaker(), Tanner(),
        Villager(), Villager(), Villager()
    ]
    role_pool_for_this_many_players = global_role_pool[:num_players + 3]
    return role_pool_for_this_many_players


def assign_roles(players: List["Player"], roles_in_game: List[Role]) -> List[Role]:
    roles = roles_in_game[:]
    random.shuffle(roles)

    for player, role in zip(players, roles[:len(players)]):
        player.set_role(role)

    return roles[len(players):]  # Return unused roles
