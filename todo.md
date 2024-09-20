Hi, we have a social deduction game app with llm opponents.
Back will have a fastapi server with websockets for rooms of games and running the game logic.

Pocketbase for auth and game logging https://app.pockethost.io/app/instances/a0tmyno1kb135kr

Front uses svelte https://www.shadcn-svelte.com/docs/changelog
Game is mostly a chatlog.
Each player should have a unique readable text color. Choices should be given through a list of buttons.


Todo:
- one_night_ultimate_werewolf/game.py should always be runnable for a local game using the dev api key.
- There's no proper testing. Any calls to apis should be avoidable with minimal code changes.  
- game_manager, game, and game_state are all overlapping in responsibilities. Eg all of them have `players`. Clean things up as much as possible and remove one if that's reasonable.
- websocket management is spread out between app and webplayer. Maybe it could mostly be moved to webapi player?
