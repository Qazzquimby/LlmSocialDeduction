<!-- App.svelte -->
<script>
  import { onMount } from 'svelte';

  let messages = [];
  let newMessage = '';
  let username = '';
  let ws;

  onMount(() => {
    ws = new WebSocket('ws://localhost:8000/ws');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      messages = [...messages, data];
    };

    return () => {
      ws.close();
    };
  });

  function sendMessage() {
    if (newMessage.trim() && username.trim()) {
      const message = {
        username: username,
        message: newMessage
      };
      ws.send(JSON.stringify(message));
      newMessage = '';
    }
  }
</script>

<main>
  <h1>Chat App</h1>

  <div class="username-input">
    <input bind:value={username} placeholder="Enter your username" />
  </div>

  <div class="chat-container">
    {#each messages as message}
      <div class="message">
        <strong>{message.username}:</strong> {message.message}
      </div>
    {/each}
  </div>

  <div class="message-input">
    <input bind:value={newMessage} placeholder="Type a message" on:keypress={(e) => e.key === 'Enter' && sendMessage()} />
    <button on:click={sendMessage}>Send</button>
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

  .message-input {
    display: flex;
  }

  input {
    flex-grow: 1;
    margin-right: 10px;
  }
</style>