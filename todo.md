Hi, we have a social deduction game app with llm opponents.
Back will have a fastapi server with websockets for rooms of games and running the game logic.

Pocketbase for auth and game logging https://app.pockethost.io/app/instances/a0tmyno1kb135kr

Front uses svelte https://www.shadcn-svelte.com/docs/changelog
Game is mostly a chatlog.
Each player should have a unique readable text color. Choices should be given through a list of
buttons.

Todo:

- Right now a lot of code in game_manager (and elsewhere?) is using user_id. The user is now
  identified by a UserLogin which should probably give players a unique id based on their openrouter
  auth. Maybe a hash of the api key? Maybe that could be a property of userLogin? Contradict me if
  this is insecure.
- There's no proper testing. Any calls to apis should be avoidable with minimal code changes.
- game_manager owns game and game owns game_manager. Yuck. Simplify how the game logic can reach the
  websockets
- websocket management is spread out between app and webplayer. Maybe it could mostly be moved to
  webapi player?
