<script lang="ts">
  import { onMount } from 'svelte';
  import { Button } from "$lib/components/ui/button";

  let messages: Array<{ username: string; message: string }> = [];
  let newMessage = '';
  let username = '';
  let ws: WebSocket;
  let gameState: string | null = null;
  let choices: string[] = [];
  let numPlayers = 4;
  let isConnected = false;

  function connectWebSocket() {
    ws = new WebSocket(`ws://localhost:8000/ws/${username}`);

    ws.onopen = () => {
      isConnected = true;
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleServerMessage(data);
    };

    ws.onclose = () => {
      isConnected = false;
      console.log('WebSocket disconnected. Attempting to reconnect...');
      setTimeout(connectWebSocket, 1000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  onMount(() => {
    if (username) {
      connectWebSocket();
    }
  });

  function handleServerMessage(data: any) {
    switch (data.type) {
      case 'game_started':
        gameState = 'Game started';
        messages = [...messages, { username: 'System', message: `Game started with players: ${data.players.join(', ')}` }];
        break;
      case 'phase':
        gameState = `${data.phase} phase`;
        messages = [...messages, { username: 'System', message: `${data.phase} phase started` }];
        break;
      default:
        messages = [...messages, { username: 'System', message: data.message }];
        break;
    }
  }

  function createAndStartGame() {
    if (isConnected) {
      ws.send(JSON.stringify({ type: 'new_game', num_players: numPlayers }));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  function sendMessage() {
    if (newMessage.trim() && isConnected) {
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

  function makeChoice(choice: string) {
    if (isConnected) {
      const message = {
        type: 'player_action',
        player: username,
        action: choice
      };
      ws.send(JSON.stringify(message));
    }
  }

  function getMessageColor(username: string): string {
    let hash = 0;
    for (let i = 0; i < username.length; i++) {
      hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = hash % 360;
    return `hsl(${hue}, 70%, 40%)`;
  }

  function handleUsernameInput() {
    if (username && !isConnected) {
      connectWebSocket();
    }
  }
</script>

<main>
  <h1>One Night Ultimate Werewolf</h1>

  <div class="username-input">
    <input bind:value={username} placeholder="Enter your username" on:change={handleUsernameInput} />
  </div>

  {#if !isConnected}
    <p>Disconnected...</p>
  {/if}
  <div class="game-controls">
    <input type="number" bind:value={numPlayers} min="3" max="10" />
    <Button on:click={createAndStartGame}>New Game</Button>
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
    white-space: pre-wrap;
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
