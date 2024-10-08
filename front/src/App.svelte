<script lang="ts">
    import {onMount} from 'svelte';
    import {Button} from "$lib/components/ui/button";
    import type {
        BaseMessage,
        GameConnectMessage,
        GameStartedMessage,
        PhaseMessage,
        SpeechMessage,
        PromptMessage,
        NextSpeakerMessage,
        BaseEvent, GameEndedMessage, PromptChoice
    } from '$lib/types';
    import {formatDistanceToNow} from 'date-fns';
    import {Toaster} from "$lib/components/ui/sonner";
    import {toast} from "svelte-sonner";

    import {writable} from 'svelte/store';

    let messages = writable<BaseMessage[]>([]);
    let newMessage = '';
    let username = 'Human';
    let ws: WebSocket;
    let gameState: string | null = null;
    let choices: PromptChoice[] = [];
    let numPlayers = 5;
    let isConnected = false;
    let gameId: string | null = localStorage.getItem('gameId');
    let prevGameId: string | null = null;
    let isPrompted = false;
    let currentSpeaker: string | null = null;
    let isGameEnded = false;

    let players: string[] = [];
    let apiKey: string | null = null;

    const serverRoot = import.meta.env.VITE_SERVER_ROOT;
    console.log("server root at ", serverRoot)

    function mapServerUrl(url: string): string {
        if (url.startsWith('ws://') || url.startsWith('wss://')) {
            return url;
        }
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        if (url.startsWith('/')) {
            return `${wsProtocol}//${window.location.host}${url}`;
        }
        return url.replace(/^http:/, wsProtocol).replace(/^https:/, wsProtocol);
    }

    function mapHttpUrl(url: string): string {
        if (url.startsWith('http://') || url.startsWith('https://')) {
            return url;
        }
        const httpProtocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
        if (url.startsWith('/')) {
            return `${httpProtocol}//${window.location.host}${url}`;
        }
        return url.replace(/^ws:/, httpProtocol).replace(/^wss:/, httpProtocol);
    }

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

    async function logout() {
        localStorage.removeItem('apiKey')
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
                    localStorage.setItem('apiKey', apiKey!); // Store the API key
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

        if (apiKey) {
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
        const url = mapServerUrl(`${serverRoot}/ws/${username}?api_key=${apiKey}`);
        ws = new WebSocket(url);

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

    async function startNewGame() {
        if (!isConnected) {
            console.error('WebSocket not connected');
            return;
        }

        try {
            const response = await fetch(mapHttpUrl(`${serverRoot}/start_game`), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({name: username, api_key: apiKey}),
            });

            if (!response.ok) {
                throw new Error('Failed to start new game');
            }

            const data = await response.json();
            gameId = data.gameId;
            localStorage.setItem('gameId', gameId!);
        } catch (error) {
            console.error('Error starting new game:', error);
        }
    }

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


    let chatInput: HTMLInputElement;

    function handleServerMessage(message: BaseEvent) {
        const handlers: { [key: string]: (msg: any) => void } = {
            "game_connect": (msg: GameConnectMessage) => {
                isConnected = true;
                if (gameId !== msg.gameId) {
                    messages.set([]);
                    gameId = msg.gameId;
                    if (gameId) {
                        localStorage.setItem('gameId', gameId);
                    } else {
                        localStorage.removeItem('gameId');
                    }
                }
            },
            'game_started': (msg: GameStartedMessage) => {
                gameState = 'Game started';
                console.log("Clearing previous chat messages")
                messages.set([{
                    type: 'game_started',
                    message: `Game started with players: ${msg.players.join(', ')}`,
                    timestamp: new Date() as string
                }]);
                players = msg.players;
            },
            'game_ended': (msg: GameEndedMessage) => {
                gameState = 'Game ended';
                messages.update(msgs => [...msgs, msg as BaseMessage]);
                toast(msg.message, {duration: 5000});
            },
            'phase': (msg: PhaseMessage) => {
                gameState = `${msg.phase} phase`;
                messages.update(msgs => [...msgs, {type: 'phase', message: `${msg.phase} phase started`}]);
            },
            'speech': (msg: SpeechMessage) => {
                messages.update(msgs => [...msgs, msg as BaseMessage]);
                currentSpeaker = null;
                isPrompted = false;
            },
            'prompt': (msg: PromptMessage) => {
                isPrompted = true;
                choices = msg.choices || [];
                multipleChoices = msg.multiple;
                minChoices = msg.min_choices;
                maxChoices = msg.max_choices;
                messages.update(msgs => [...msgs, msg as BaseMessage]);
                currentSpeaker = null;
            },
            'next_speaker': (msg: NextSpeakerMessage) => {
                currentSpeaker = msg.player;
                console.log("New currentSpeaker", currentSpeaker);
                isPrompted = currentSpeaker === username;
                if (isPrompted && chatInput) {
                    setTimeout(() => chatInput.focus(), 0);
                }
            },
        };

        const handler = handlers[message.type];
        if (handler) {
            handler(message);
        } else if ('message' in message) {
            messages.update(msgs => [...msgs, message as BaseMessage]);
        } else {
            console.warn('Received unknown message type:', message);
        }
    }

    let initialTimeLeft = 3*60;
    let timeLeft = initialTimeLeft;
    let timer: number | null = null;

    function startTimer() {
        if (timer) clearInterval(timer);
        timeLeft = initialTimeLeft;
        timer = setInterval(() => {
            timeLeft--;
            if (timeLeft <= 0) {
                clearInterval(timer);
                timer = null;
                sendMessage(true);
            }
        }, 1000);
    }

    function stopTimer() {
        if (timer) {
            clearInterval(timer);
            timer = null;
        }
    }

    $: if (isPrompted) {
        startTimer();
    } else {
        stopTimer();
    }

    function sendMessage(timeout = false) {
        if ((newMessage.trim() || timeout) && isConnected) {
            const message = {
                type: 'player_action',
                player: username,
                action: 'speak',
                message: timeout ? "(No response)" : newMessage
            };
            console.log("sending ", message)
            ws.send(JSON.stringify(message));
            newMessage = '';
            isPrompted = false;
            stopTimer();
        }
    }

    let selectedChoices: number[] = [];
    let multipleChoices = false;
    let minChoices = 1;
    let maxChoices: number | null = null;

    function toggleChoice(value: number) {
        if (multipleChoices) {
            const index = selectedChoices.indexOf(value);
            if (index === -1) {
                selectedChoices = [...selectedChoices, value];
            } else {
                selectedChoices = selectedChoices.filter(v => v !== value);
            }
        } else {
            selectedChoices = [value];
        }
    }

    function isValidSelection() {
        return selectedChoices.length >= minChoices &&
            (maxChoices === null || selectedChoices.length <= maxChoices);
    }

    function submitChoices() {
        if (isConnected && isValidSelection()) {
            const message = {
                type: 'player_action',
                player: username,
                action: 'make_choice',
                message: selectedChoices.join(',')
            };
            ws.send(JSON.stringify(message));
            selectedChoices = [];
            choices = []; // Clear choices immediately after submission
            isPrompted = false; // Set isPrompted to false after submission
            currentSpeaker = null; // Reset currentSpeaker
        }
    }

    function doNothingButton() {
        console.log("do nothing button pushed")
    }

    function debugBackButton() {
        fetch(mapHttpUrl(`${serverRoot}/debug`))
            .then(response => response.text())
            .then(data => console.log(data))
            .catch(error => console.error(error));
    }

    function leaveGame() {
        if (ws && isConnected) {
            const message = {
                type: 'player_action',
                player: username,
                action: 'leave_game'
            };
            ws.send(JSON.stringify(message));
        }
        gameId = null;
        localStorage.removeItem('gameId');
        messages.set([]);
        gameState = null;
        choices = [];
        players = [];
        isGameEnded = false;
        if (ws) {
            ws.close();
        }
    }

    $: if (gameId && prevGameId && gameId !== prevGameId) {
        console.log(`gameId changed from ${prevGameId} to ${gameId}`);
        toast(`Previous game shut down. Making a new game.`, {duration: 5000});
        prevGameId = gameId;
    }

    $: console.log("Debug messages", $messages)

    let messageContainer: HTMLDivElement;

    function scrollToBottom() {
        if (messageContainer) {
            messageContainer.scrollTop = messageContainer.scrollHeight;
        }
    }

    $: if ($messages.length) {
        setTimeout(scrollToBottom, 0);
    }

</script>

<Toaster/>
<main bg-dark-900 text-gray-100 flex="~ col" h-screen font-sans overflow-hidden>
    <div max-w-3xl p-4 w-full mx-auto flex="~ col" h-full>
        <h1 text-3xl text-center font-bold mb-6 text-shadow-sm text-shadow-neon-blue font-mono>
            <span text-gray-400>t r</span> <span>a i</span> <span text-gray-400>t o r</span>
        </h1>

        {#if !apiKey}
            <!--is logged out-->
            <div>
                <p>A WIP engine for social deduction games with LLMs.</p>
                <p>Right now only One Night Ultimate Werewolf is set up.</p>
                <p mt-1rem>
                    Running LLMs costs money so to play you have to link an OpenRouter account with an api key.
                    You can set a small limit on the key.</p>

                <Button style="width:100%" on:click={login}>Login with OpenRouter</Button>
            </div>
        {:else}
            <div ml-auto flex="~ col" items-end>
                <Button on:click={logout}>Log out</Button>

                <div>
                    <span>Server: </span>
                    {#if isConnected}
                        <span class="text-green-400">Connected</span>
                        {#if gameId}
                            <span>to {gameId}</span>
                            <Button on:click={leaveGame}>Leave Game</Button>
                        {/if}
                    {:else}
                        <span text-red-400>Disconnected</span>
                        {#if gameId}
                            <span>from {gameId}</span>
                        {/if}
                    {/if}
                </div>


            </div>
            {#if gameId}
                <div w-full flex="~ col" h-full min-h-0>
                    <div mb-4 flex-shrink-0 flex justify-between items-center>
                        {#if gameState}
                            <p bg-dark-800 p-2 rounded text-lg capitalize>{gameState}</p>
                        {/if}
                        {#if isGameEnded}
                            <Button on:click={leaveGame}>Exit Game</Button>
                        {/if}
                    </div>

                    <div bind:this={messageContainer} flex-grow overflow-y-auto bg-dark-800
                         rounded p-4 mb-4 style="scroll-behavior: smooth;">
                        {#each $messages as {type, username, message, timestamp}, i}
                            {#if username && type === "speech"}
                                <div class="message"
                                     class:first-message={i === 0 || $messages[i-1].username !== username}>
                                    {#if i === 0 || $messages[i - 1].username !== username}
                                        <div class="message-header"
                                             style="color: {formatOKLCH(playerColors.get(username))}">
                                            <strong>{username}</strong>
                                            <span class="text-xs text-gray-500 ml-2">{formatDistanceToNow(new Date(timestamp), {addSuffix: true})}</span>
                                        </div>
                                    {/if}
                                    <div class="message-content">
                                        {message}
                                    </div>
                                </div>
                            {:else}
                                <div class="system-message">
                                    {message}
                                </div>
                            {/if}
                        {/each}
                    </div>

                    <div class="interaction-area" bg-dark-800 p-4 rounded mb-4>
                        {#if currentSpeaker && currentSpeaker !== username}
                            <div italic text-gray-400>
                                {currentSpeaker} is typing...
                            </div>
                        {:else if choices.length > 0}
                            <div class="choices-container">
                                <p>{$messages[$messages.length - 1].message}</p>
                                {#if multipleChoices}
                                    {#each choices as {index, name}}
                                        <label class="checkbox-container">
                                            <input type="checkbox" 
                                                   checked={selectedChoices.includes(index)}
                                                   on:change={() => toggleChoice(index)}
                                            />
                                            {name}
                                        </label>
                                    {/each}
                                    <Button
                                        on:click={submitChoices}
                                        disabled={!isValidSelection()}
                                    >
                                        Submit
                                    </Button>
                                {:else}
                                    {#each choices as {index, name}}
                                        <Button on:click={() => {
                                            selectedChoices = [index];
                                            submitChoices();
                                        }}>
                                            {name}
                                        </Button>
                                    {/each}
                                {/if}
                            </div>
                        {:else if isPrompted}
                            <div flex="~ col" gap-2>
                                <div flex items-center justify-between>
                                    <span>Time left: {timeLeft}s</span>
                                    <Button on:click={sendMessage}>Send</Button>
                                </div>
                                <input
                                    bind:value={newMessage}
                                    bind:this={chatInput}
                                    placeholder="Type a message"
                                    on:keypress={(e) => e.key === 'Enter' && sendMessage()}
                                    bg-dark-700
                                    text-gray-100
                                    border-gray-600
                                    rounded
                                    p-2
                                    flex-grow
                                    disabled={timeLeft <= 0}
                                />
                            </div>
                        {:else if $messages[$messages.length - 1]?.type === 'prompt' && $messages[$messages.length - 1].message.includes("Are you ready to start the night phase?")}
                            <div>
                                <Button on:click={() => submitChoices()}>
                                    Start Night Phase
                                </Button>
                            </div>
                        {:else}
                            <div italic text-gray-400>
                                Wheels are in motion...
                            </div>
                        {/if}
                    </div>
                </div>

            {:else}
                <div flex="~ col" mt-4rem>
                    <div class="game-card" bg-dark-800 p-4 rounded-lg mb-4 flex="~ wrap" items-center>
                        <div min-w-12rem max-w-24rem>
                            <h2 text-xl font-bold mb-2>One Night Ultimate Werewolf</h2>
                            <p text-gray-400>A single round of night actions, talking, and voting.</p>
                        </div>
                        <div mx-1rem flex-grow flex items-center>
                            <Button class="w-full px-2rem py-1rem bg-blue" on:click={startNewGame}>Start New Game
                            </Button>
                        </div>
                    </div>
                </div>
            {/if}

        {/if}
<!--        <div flex gap-2 mt-4>-->
<!--            <Button on:click={doNothingButton}>Do Nothing</Button>-->
<!--            <Button on:click={debugBackButton}>Debug Back</Button>-->
<!--        </div>-->
    </div>
</main>

<style>
    .game-card {
        border: 1px solid #4a5568;
        transition: all 0.3s ease;
    }

    .game-card:hover {
        transform: scale(1.01);
        box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
    }

    .interaction-area {
        transition: all 0.3s ease;
    }

    .message {
        margin-bottom: 4px;
    }

    .message-header {
        margin-top: 8px;
        font-weight: bold;
    }

    .message-content {
        padding-left: 8px;
    }

    .system-message {
        margin-bottom: 8px;
        font-style: italic;
        color: #a0aec0;
        white-space: pre-wrap;
    }

    .first-message {
        margin-top: 8px;
    }
</style>
