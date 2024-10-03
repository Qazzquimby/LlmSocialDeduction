Hi, we have a social deduction game app with llm opponents.
Back will have a fastapi server with websockets for rooms of games and running the game logic.

Pocketbase for auth and game logging https://app.pockethost.io/app/instances/a0tmyno1kb135kr

Front uses svelte https://www.shadcn-svelte.com/docs/changelog
Game is mostly a chatlog.
Each player should have a unique readable text color. Choices should be given through a list of
buttons.

Todo:

# AI:
Do rules error checking before sending and allow them to change their answer

Optimize message history to shorten. Eg remove their past speechs from history since they already see the my_action event

# Unconfirmed:
On a ws reconnect, the server somehow got a message from Human which I didn't write. It was a duplicate of the previous message.
2024-10-02 13:24:51.231 | INFO     | player:print:211 - informing Human with type='next_speaker' player='Robby'
2024-10-02 13:25:08.185 | INFO     | player:print:211 - informing Human with type='speech' message="I want to share that I tapped Human last night as the Thing. Human, could you confirm whether you were tapped? This information could help guide our discussions today. Let's work together to identify any threats and keep the game fun and fair for everyone!" username='Robby' timestamp='2024-10-02T13:25:08.168794'
2024-10-02 13:25:08.197 | INFO     | player:print:211 - informing Human with type='next_speaker' player='Human'
2024-10-02 13:25:28.784 | INFO     | player:print:211 - informing Human with type='speech' message="I want to share that I tapped Human last night as the Thing. Human, could you confirm whether you were tapped? This information could help guide our discussions today. Let's work together to identify any threats and keep the game fun and fair for everyone!" username='Human' timestamp='2024-10-02T13:25:28.784866'

Sometimes messages dont arrive until I refresh. Usually the chat just says "No active games"

# A bit ugly but less critical:
Refreshing seems to shuffle messages a bit. Usually a speech message appears up with the rules at the top.

Human connects many times at once in logs. On disconnecting they all disconnect.

Refreshing while server is waiting for player to start the game removes the start game prompt.

If in a game with only messages saying "game ended", automatically exit game