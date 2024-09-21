import pytest

from games.one_night_ultimate_werewolf.game import OneNightWerewolf
from player import AIPlayer
from websockets import UserLogin


@pytest.fixture
def game():
    return OneNightWerewolf(num_players=5, has_human=False)


def test_game_setup(game):
    assert game.num_players == 5
    assert not game.has_human
    assert game.state is not None


@pytest.mark.asyncio
async def test_game_setup_with_human():
    login = UserLogin(name="TestUser", api_key="test_api_key")
    game = OneNightWerewolf(num_players=5, has_human=True, login=login)
    await game.setup_game()
    assert len(game.state.players) == 5
    assert any(isinstance(player, AIPlayer) for player in game.state.players)
    assert any(player.name == "TestUser" for player in game.state.players)


# Add more tests as needed
