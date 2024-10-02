Hi, we have a social deduction game app with llm opponents.
Back will have a fastapi server with websockets for rooms of games and running the game logic.

Pocketbase for auth and game logging https://app.pockethost.io/app/instances/a0tmyno1kb135kr

Front uses svelte https://www.shadcn-svelte.com/docs/changelog
Game is mostly a chatlog.
Each player should have a unique readable text color. Choices should be given through a list of
buttons.

Todo:

On a ws reconnect, the server somehow got a message from Human which I didn't write. It was a duplicate of the previous message.
2024-10-02 13:24:51.231 | INFO     | player:print:211 - informing Human with type='next_speaker' player='Robby'
2024-10-02 13:25:08.185 | INFO     | player:print:211 - informing Human with type='speech' message="I want to share that I tapped Human last night as the Thing. Human, could you confirm whether you were tapped? This information could help guide our discussions today. Let's work together to identify any threats and keep the game fun and fair for everyone!" username='Robby' timestamp='2024-10-02T13:25:08.168794'
2024-10-02 13:25:08.197 | INFO     | player:print:211 - informing Human with type='next_speaker' player='Human'
2024-10-02 13:25:28.784 | INFO     | player:print:211 - informing Human with type='speech' message="I want to share that I tapped Human last night as the Thing. Human, could you confirm whether you were tapped? This information could help guide our discussions today. Let's work together to identify any threats and keep the game fun and fair for everyone!" username='Human' timestamp='2024-10-02T13:25:28.784866'

Text box appeared at start of game when it wasnt my turn to speak

Sometimes messages dont arrive until I refresh. Usually the chat just says "No active games"

Human connects many times at once in logs. On disconnecting they all disconnect.

Refreshing while server is waiting for player to start the game removes the start game prompt.

After performing night action it displayed the text box and timer. Same after voting, maybe after any button submission.

rules missing whitespace