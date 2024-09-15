<script lang="ts">
  import { onMount } from 'svelte';
  import { Button } from "$lib/components/ui/button";
  import type {
    BaseMessage,
    GameConnectMessage,
    GameStartedMessage,
    PhaseMessage,
    SpeechMessage,
    PromptMessage,
    NextSpeakerMessage,
    PlayerActionMessage,
    BaseEvent
  } from '$lib/types';

  let messages: BaseMessage[] = [];
  let newMessage = '';
  let username = '';
  let ws: WebSocket;
  let gameState: string | null = null;
  let choices: string[] = [];
  let numPlayers = 5;
  let isConnected = false;
  let gameId: string | null = null;
  let isPrompted = false;
  let currentSpeaker: string | null = null;

  let players: string[] = [];

  function connectWebSocket() {
    console.log('Trying connection');
    ws = new WebSocket(`ws://localhost:8000/ws/${username}`);

    ws.onopen = () => {
      isConnected = true;
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("new message", data)
      handleServerMessage(data);
    };

    ws.onclose = () => {
      isConnected = false;
      if (username) {
        console.log('Disconnected, attempting reconnect for ', username);
        setTimeout(connectWebSocket, 1000);
      }

    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  onMount(() => {
    if (username) {
      connectWebSocket();
    }
    return () => {
      if (ws) {
        console.log("Closing websocket")
        ws.close();
      }
    };
  });


  //color
  type OKLCHColor = [number, number, number]; // [lightness, chroma, hue]

  function generateColors(count: number, baseLightness: number = 73): OKLCHColor[] {
      const colors: OKLCHColor[] = [];
      const goldenRatioConjugate = 0.618033988749895;
      let hue = Math.random();

      for (let i = 0; i < count; i++) {
          hue += goldenRatioConjugate;
          hue %= 1;

          // Vary lightness slightly to improve distinguishability
          const lightness = baseLightness + (Math.random() * 10 - 5);

          // Use a fixed chroma for simplicity, but you can vary this too if needed
          const chroma = 0.216;

          colors.push([lightness, chroma, hue * 360]);
      }

      return colors;
  }

  function getContrastColor(color: OKLCHColor): 'black' | 'white' {
      const [lightness] = color;
      // A simple threshold-based approach
      return lightness > 60 ? 'black' : 'white';
  }

  function formatOKLCH(color: OKLCHColor): string {
      const [l, c, h] = color;
      return `oklch(${l.toFixed(0)}% ${c.toFixed(3)} ${h.toFixed(0)})`;
  }

  $: playerColorList = generateColors(numPlayers)
  $: playerColors = new Map(players.map((player, i) => [player, playerColorList[i]]));
  $: playerContrastColors = new Map(
    players.map((player) => [player, getContrastColor(playerColors.get(player)!)])
);
  // /color



  function handleServerMessage(message: BaseEvent) {
    const handlers: { [key: string]: (msg: any) => void } = {
      "game_connect": (msg: GameConnectMessage) => {
        isConnected = true;
        gameId = msg.gameId;
      },
      'game_started': (msg: GameStartedMessage) => {
        gameState = 'Game started';
        messages.push({ type: 'game_started', message: `Game started with players: ${msg.players.join(', ')}` });
        players = msg.players;
      },
      'phase': (msg: PhaseMessage) => {
        gameState = `${msg.phase} phase`;
        messages.push({ type: 'phase', message: `${msg.phase} phase started` });
      },
      'speech': (msg: SpeechMessage) => {
        messages.push(msg as BaseMessage)
        currentSpeaker = null;
      },
      'prompt': (msg: PromptMessage) => {
        isPrompted = true;
        messages.push(msg as BaseMessage);
      },
      'next_speaker': (msg: NextSpeakerMessage) => {
        currentSpeaker = msg.player;
      }
    };

    const handler = handlers[message.type];
    if (handler) {
      handler(message);
    } else if ('message' in message) {
      messages = [...messages, message as BaseMessage];
    } else {
      console.warn('Received unknown message type:', message);
    }
  }

  function newGame() {
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
      console.log("sending ", message)
      ws.send(JSON.stringify(message));
      newMessage = '';
      isPrompted = false;
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

  function handleUsernameInput() {
    if (username && !isConnected) {
      connectWebSocket();
    }
  }

  $: gameId && (() => {
    console.log("gameId changed to ", gameId, "clearing messages")
    messages = []
  });

</script>

<main>
  <h1>One Night Ultimate Werewolf</h1>

  <div class="username-input">
    <input bind:value={username} placeholder="Enter your username" on:change={handleUsernameInput} />
  </div>

  {#if isConnected}
    <span>Connected </span>
    {#if gameId}
      <span>to {gameId}</span>
    {/if}
  {:else}
    <span>Disconnected </span>
    {#if gameId}
      <span>from {gameId}</span>
    {/if}
  {/if}
  <div class="game-controls">
    <input type="number" bind:value={numPlayers} min="3" max="10" />
    <Button on:click={newGame}>New Game</Button>
  </div>

  <div class="game-state">
    {#if gameState}
      <p>Current game state: {gameState}</p>
    {/if}
  </div>

  <div class="chat-container">
    {#each messages as message}
      {#if message.username && message.type === "speech"}
        <div class="message player-message" style="background-color: {formatOKLCH(playerColors.get(message.username))}; color: {playerContrastColors.get(message.username)}">
          <strong>{message.username}:</strong> {message.message}
        </div>
      {:else}
        <div class="message system-message">
          <strong>System:</strong> {message.message}
        </div>
      {/if}
    {/each}
    {#if currentSpeaker}
      <div class="current-speaker">
        {currentSpeaker} is thinking...
      </div>
    {/if}
  </div>

  {#if isPrompted}
    <div class="message-input">
      <input bind:value={newMessage} placeholder="Type a message" on:keypress={(e) => e.key === 'Enter' && sendMessage()} />
      <Button on:click={sendMessage}>Send</Button>
    </div>
  {/if}

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

  .player-message {
    padding: 5px;
    border-radius: 5px;
  }

  .system-message {
    color: black;
    font-style: italic;
  }

  .current-speaker {
    font-style: italic;
    color: #666;
    margin-top: 10px;
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
