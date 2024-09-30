Hi, we have a social deduction game app with llm opponents.
Back will have a fastapi server with websockets for rooms of games and running the game logic.

Pocketbase for auth and game logging https://app.pockethost.io/app/instances/a0tmyno1kb135kr

Front uses svelte https://www.shadcn-svelte.com/docs/changelog
Game is mostly a chatlog.
Each player should have a unique readable text color. Choices should be given through a list of
buttons.

Todo:

- When an invalid input is entered, we should pick a random valid action rather than doing nothing.
- If a webplayer doesn't enter a message in time, they still have their textbox. Not sure whats good UX here. It doesn't show their time limit or anything.
- When its the user's turn to speak, if they refresh (disconnect reconnect) they aren't given the chat bar to enter text.
