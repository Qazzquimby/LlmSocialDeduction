Hi, we have a social deduction game app with llm opponents.
Back will have a fastapi server with websockets for rooms of games and running the game logic.

Pocketbase for auth and game logging https://app.pockethost.io/app/instances/a0tmyno1kb135kr

Front uses svelte https://www.shadcn-svelte.com/docs/changelog
Game is mostly a chatlog.
Each player should have a unique readable text color. Choices should be given through a list of
buttons.

Todo:

- When its your turn to talk, chatbox shows "Human is typing..." rather than freeing the text box.
- Buttons should be in place of the text box. They should get a chatbox or buttons, not both.
- If its choose single, they shouldnt need a submit button.
- If its choose mulptiple it should be tickboxes with a submit button
- Speech timer doesn't count down.
