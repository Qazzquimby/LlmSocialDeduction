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
        console.log("Clearing previous chat messages")
        messages = [{ type: 'game_started', message: `Game started with players: ${msg.players.join(', ')}` }];
        players = msg.players;
      },
      'phase': (msg: PhaseMessage) => {
        gameState = `${msg.phase} phase`;
        messages = [...messages, { type: 'phase', message: `${msg.phase} phase started` }];
      },
      'speech': (msg: SpeechMessage) => {
        messages = [...messages, msg as BaseMessage];
        currentSpeaker = null;
      },
      'prompt': (msg: PromptMessage) => {
        isPrompted = true;
        messages = [...messages, msg as BaseMessage];
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

  function doNothingButton() {
    console.log("do nothing button pushed")
  }

  function debugBackButton() {
    fetch("http://localhost:8000/debug")
      .then(response => response.text())
      .then(data => console.log(data))
      .catch(error => console.error(error));
  }

</script>

<main bg="dark-800" text="gray-100" min-h-screen flex="~ col" p="4">
  <h1 text="3xl center" font="bold" mb="6" text-shadow="sm neon-blue">One Night Ultimate Werewolf</h1>

  <div mb="4">
    <input 
      bind:value={username} 
      placeholder="Enter your username" 
      on:change={handleUsernameInput}
      bg="dark-700"
      text="gray-100"
      border="1 gray-600"
      rounded
      p="2"
      w="full"
    />
  </div>

  <div mb="4" flex="~ gap-2" items-center>
    {#if isConnected}
      <span text="green-400">Connected</span>
      {#if gameId}
        <span>to {gameId}</span>
      {/if}
    {:else}
      <span text="red-400">Disconnected</span>
      {#if gameId}
        <span>from {gameId}</span>
      {/if}
    {/if}
  </div>

  <div class="game-controls" flex="~ wrap gap-2" mb="4">
    <input 
      type="number" 
      bind:value={numPlayers} 
      min="3" 
      max="10"
      bg="dark-700"
      text="gray-100"
      border="1 gray-600"
      rounded
      p="2"
      w="16"
    />
    <Button on:click={newGame} bg="indigo-600" hover="bg-indigo-700">New Game</Button>
    <Button on:click={doNothingButton} bg="gray-600" hover="bg-gray-700">Do Nothing</Button>
    <Button on:click={debugBackButton} bg="purple-600" hover="bg-purple-700">Debug Back</Button>
  </div>

  <div mb="4">
    {#if gameState}
      <p bg="dark-700" p="2" rounded text="lg">Current game state: {gameState}</p>
    {/if}
  </div>

  <div flex-grow overflow-y-auto bg="dark-700" rounded p="4" mb="4">
    {#each messages as message}
      {#if message.username && message.type === "speech"}
        <div 
          mb="2" 
          p="2" 
          rounded 
          style="background-color: {formatOKLCH(playerColors.get(message.username))}; color: {playerContrastColors.get(message.username)}"
        >
          <strong>{message.username}:</strong> {message.message}
        </div>
      {:else}
        <div mb="2" italic text="gray-400">
          <strong>System:</strong> {message.message}
        </div>
      {/if}
    {/each}
    {#if currentSpeaker}
      <div mt="2" italic text="gray-400">
        {currentSpeaker} is thinking...
      </div>
    {/if}
  </div>

  {#if isPrompted}
    <div flex="~ gap-2" mb="4">
      <input 
        bind:value={newMessage} 
        placeholder="Type a message" 
        on:keypress={(e) => e.key === 'Enter' && sendMessage()}
        bg="dark-700"
        text="gray-100"
        border="1 gray-600"
        rounded
        p="2"
        flex-grow
      />
      <Button on:click={sendMessage} bg="green-600" hover="bg-green-700">Send</Button>
    </div>
  {/if}

  <div flex="~ wrap gap-2">
    {#each choices as choice}
      <Button on:click={() => makeChoice(choice)} bg="blue-600" hover="bg-blue-700">{choice}</Button>
    {/each}
  </div>
</main>
