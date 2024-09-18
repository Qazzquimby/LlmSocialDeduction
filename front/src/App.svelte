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
        BaseEvent
    } from '$lib/types';

    let messages: BaseMessage[] = [
        {
            type: "phase",
            message: "This is an important announcement",
            username: "System"
        },
        {
            type: "speech",
            message: "Blah",
            username: "Ricky"
        }
    ];
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
    let apiKey: string | null = null;
    let isDev: boolean = false; // Add this line to control dev mode

    async function sha256CodeChallenge(input: string) {
        const encoder = new TextEncoder();
        const data = encoder.encode(input);
        const hash = await crypto.subtle.digest('SHA-256', data);
        return btoa(String.fromCharCode(...new Uint8Array(hash)))
            .replace(/=/g, '')
            .replace(/\+/g, '-')
            .replace(/\//g, '_');
    }

    async function login() {
        const codeVerifier = crypto.randomUUID();
        const codeChallenge = await sha256CodeChallenge(codeVerifier);
        const callbackUrl = encodeURIComponent(window.location.origin);
        const authUrl = `https://openrouter.ai/auth?callback_url=${callbackUrl}&code_challenge=${codeChallenge}&code_challenge_method=S256`;
        
        // Store code_verifier in localStorage (you might want to use a more secure method in production)
        localStorage.setItem('code_verifier', codeVerifier);
        
        // Redirect to OpenRouter auth page
        window.location.href = authUrl;
    }

    async function exchangeCodeForKey(code: string, codeVerifier: string) {
        const response = await fetch('https://openrouter.ai/api/v1/auth/keys', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code,
                code_verifier: codeVerifier,
                code_challenge_method: 'S256',
            }),
        });

        if (!response.ok) {
            throw new Error('Failed to exchange code for API key');
        }

        const data = await response.json();
        return data.key;
    }

    onMount(async () => {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        
        if (code) {
            const codeVerifier = localStorage.getItem('code_verifier');
            if (codeVerifier) {
                try {
                    apiKey = await exchangeCodeForKey(code, codeVerifier);
                    localStorage.setItem('apiKey', apiKey); // Store the API key
                    localStorage.removeItem('code_verifier');
                    // Remove the code from the URL
                    window.history.replaceState({}, document.title, window.location.pathname);
                } catch (error) {
                    console.error('Error exchanging code for API key:', error);
                }
            }
        } else {
            // Check if we have a stored API key
            apiKey = localStorage.getItem('apiKey');
        }

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

    function connectWebSocket() {
        console.log('Trying connection');
        ws = new WebSocket(`ws://localhost:8000/ws/${username}?apiKey=${apiKey}&isDev=${isDev}`);

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
        try {
            const [l, c, h] = color;
            return `oklch(${l.toFixed(0)}% ${c.toFixed(3)} ${h.toFixed(0)})`;
        } catch (TypeError) {
            return 'black';
        }

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
                messages = [{type: 'game_started', message: `Game started with players: ${msg.players.join(', ')}`}];
                players = msg.players;
            },
            'phase': (msg: PhaseMessage) => {
                gameState = `${msg.phase} phase`;
                messages = [...messages, {type: 'phase', message: `${msg.phase} phase started`}];
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
            ws.send(JSON.stringify({type: 'new_game', num_players: numPlayers}));
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

<main bg-dark-900 text-gray-100 min-h-screen flex-col p-4 items-center font-sans>
    <div max-w-3xl p-4 w-full>
        <h1 text-3xl text-center font-bold mb-6 text-shadow-sm text-shadow-neon-blue>One Night Ultimate Werewolf</h1>

        {#if !apiKey}
            <Button on:click={login}>Login with OpenRouter</Button>
        {:else}
            <div mb-4 flex gap-2 items-center justify-between>
                <div flex gap-2 items-center>
                    <input
                            bind:value={username}
                            placeholder="Username"
                            on:change={handleUsernameInput}
                            bg-dark-800
                            text-gray-100
                            border-gray-700
                            rounded
                            p-2
                            w-40
                    />
                    {#if isConnected}
                        <span text-green-400>Connected</span>
                        {#if gameId}
                            <span>to {gameId}</span>
                        {/if}
                    {:else}
                        <span text-red-400>Disconnected</span>
                        {#if gameId}
                            <span>from {gameId}</span>
                        {/if}
                    {/if}
                </div>


            </div>

            <div mb-4>
                {#if gameState}
                    <p bg-dark-800 p-2 rounded text-lg>Current game state: {gameState}</p>
                {/if}
            </div>

            <div flex-grow overflow-y-auto bg-dark-800 rounded p-4 mb-4 h-64>
                {#each messages as {type, username, message}}
                    {#if username && type === "speech"}
                        <div
                                mb-2
                                p-2
                                rounded
                                style="background-color: {formatOKLCH(playerColors.get(username))}; color: {playerContrastColors.get(username)}"
                        >
                            <strong>{username}:</strong> {message}
                        </div>
                    {:else}
                        <div mb-2 italic text-gray-400>
                            <strong>System:</strong> {message}
                        </div>
                    {/if}
                {/each}
                {#if currentSpeaker}
                    <div mt-2 italic text-gray-400>
                        {currentSpeaker} is thinking...
                    </div>
                {/if}
            </div>

            {#if isPrompted}
                <div flex gap-2 mb-4>
                    <input
                            bind:value={newMessage}
                            placeholder="Type a message"
                            on:keypress={(e) => e.key === 'Enter' && sendMessage()}
                            bg-dark-800
                            text-gray-100
                            border-gray-700
                            rounded
                            p-2
                            flex-grow
                    />
                    <Button on:click={sendMessage}>Send</Button>
                </div>
            {/if}

            <div flex flex-wrap gap-2>
                {#each choices as choice}
                    <Button on:click={() => makeChoice(choice)}>{choice}</Button>
                {/each}
            </div>

        {/if}
        <div flex gap-2 mt-4>
            <Button on:click={doNothingButton}>Do Nothing</Button>
            <Button on:click={debugBackButton}>Debug Back</Button>
        </div>
    </div>
</main>
