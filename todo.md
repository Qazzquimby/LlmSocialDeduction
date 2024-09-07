Hi, we have a social deduction game app with llm opponents.
Back will have a fastapi server with websockets for rooms of games and running the game logic.

Pocketbase for auth and game logging https://app.pockethost.io/app/instances/a0tmyno1kb135kr

Front uses svelte https://www.shadcn-svelte.com/docs/changelog
Game is mostly a chatlog.
Each player should have a unique readable text color. Choices should be given through a list of buttons.


Tasks:
- [ ] Right now the game logic is specific to ONUW but it should be more general for future games added.
- [ ] The front is just a bare svelte chat app. Front and back need to be modified to talk to each other.