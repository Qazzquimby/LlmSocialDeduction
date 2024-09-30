Hi, we have a social deduction game app with llm opponents.
Back will have a fastapi server with websockets for rooms of games and running the game logic.

Pocketbase for auth and game logging https://app.pockethost.io/app/instances/a0tmyno1kb135kr

Front uses svelte https://www.shadcn-svelte.com/docs/changelog
Game is mostly a chatlog.
Each player should have a unique readable text color. Choices should be given through a list of
buttons.

Todo:

- nextspeaker messages arrive without showing the player who's next to speak. It's undefined in the frontend like a BaseMessage.
- when player is prompted to speak, cursor should jump to the chat bar so they can start typing without needing to click it.
- When its the user's turn to speak, if they refresh (disconnect reconnect) they aren't given the chat bar to enter text.
- integration testing is probably a good idea. AI can already be mocked out.
