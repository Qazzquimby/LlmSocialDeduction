<!-- App.svelte -->
<script>
  import { onMount } from 'svelte';
  import { Button } from '@shadcn/svelte';

  let messages = [];
  let newMessage = '';
  let username = '';
  let ws;
  let gameState = null;
  let choices = [];
  let gameId = '';
  let numPlayers = 4;

  onMount(() => {
    gameId = Math.random().toString(36).substring(7);
    ws = new WebSocket(`ws://localhost:8000/ws/${gameId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleServerMessage(data);
    };

    return () => {
      ws.close();
    };
  });

  function handleServerMessage(data) {
    switch (data.type) {
      case 'message':
        messages = [...messages, data];
        break;
      case 'game_created':
        gameState = 'Game created';
        break;
      case 'game_started':
        gameState = 'Game started';
        messages = [...messages, { username: 'System', message: `Game started with players: ${data.players.join(', ')}` }];
        break;
      case 'night_phase_completed':
        gameState = 'Night phase completed';
        messages = [...messages, { username: 'System', message: 'Night phase completed' }];
        break;
      case 'day_phase_completed':
        gameState = 'Day phase completed';
        messages = [...messages, { username: 'System', message: 'Day phase completed' }];
        break;
      case 'voting_completed':
        gameState = 'Voting completed';
        messages = [...messages, { username: 'System', message: `Voting completed. Executed players: ${data.executed.join(', ')}` }];
        break;
      case 'game_ended':
        gameState = 'Game ended';
        messages = [...messages, { username: 'System', message: 'Game ended' }];
        break;
      case 'action_result':
        messages = [...messages, { username: data.player, message: data.result }];
        break;
    }
  }

  function createGame() {
    ws.send(JSON.stringify({ type: 'create_game', num_players: numPlayers }));
  }

  function startGame() {
    ws.send(JSON.stringify({ type: 'start_game' }));
  }

  function sendMessage() {
    if (newMessage.trim() && username.trim()) {
      const message = {
        type: 'player_action',
        player: username,
        action: 'speak',
        message: newMessage
      };
      ws.send(JSON.stringify(message));
      newMessage = '';
    }
  }

  function makeChoice(choice) {
    const message = {
      type: 'player_action',
      player: username,
      action: choice
    };
    ws.send(JSON.stringify(message));
  }

  function getMessageColor(username) {
    let hash = 0;
    for (let i = 0; i < username.length; i++) {
      hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = hash % 360;
    return `hsl(${hue}, 70%, 40%)`;
  }
</script>

<main>
  <h1>One Night Ultimate Werewolf</h1>

  <div class="username-input">
    <input bind:value={username} placeholder="Enter your username" />
  </div>

  <div class="game-controls">
    <input type="number" bind:value={numPlayers} min="3" max="10" />
    <Button on:click={createGame}>Create Game</Button>
    <Button on:click={startGame}>Start Game</Button>
  </div>

  <div class="game-state">
    {#if gameState}
      <p>Current game state: {gameState}</p>
    {/if}
  </div>

  <div class="chat-container">
    {#each messages as message}
      <div class="message" style="color: {getMessageColor(message.username)}">
        <strong>{message.username}:</strong> {message.message}
      </div>
    {/each}
  </div>

  <div class="message-input">
    <input bind:value={newMessage} placeholder="Type a message" on:keypress={(e) => e.key === 'Enter' && sendMessage()} />
    <Button on:click={sendMessage}>Send</Button>
  </div>

  <div class="choices">
    {#each choices as choice}
      <Button on:click={() => makeChoice(choice)}>{choice}</Button>
    {/each}
  </div>
</main>

<style>
  main {
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
  }

  .chat-container {
    height: 400px;
    overflow-y: auto;
    border: 1px solid #ccc;
    padding: 10px;
    margin-bottom: 10px;
  }

  .message {
    margin-bottom: 5px;
  }

  .message-input, .game-controls {
    display: flex;
    margin-bottom: 10px;
    gap: 10px;
  }

  input {
    flex-grow: 1;
  }

  .choices {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .game-state {
    margin-bottom: 10px;
    font-weight: bold;
  }
</style>
