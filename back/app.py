import json
import pickle
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from games.one_night_ultimate_werewolf.game import OneNightWerewolf
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Store active connections and games
active_connections = {}
games = {}

# Function to save game state
def save_game_state(username, game):
    try:
        with open(f"game_state_{username}.pkl", "wb") as f:
            pickle.dump(game, f)
        logger.info(f"Game state saved for user: {username}")
    except Exception as e:
        logger.error(f"Error saving game state for user {username}: {str(e)}")

# Function to load game state
def load_game_state(username):
    try:
        with open(f"game_state_{username}.pkl", "rb") as f:
            game = pickle.load(f)
        logger.info(f"Game state loaded for user: {username}")
        return game
    except FileNotFoundError:
        logger.info(f"No saved game state found for user: {username}")
        return None
    except Exception as e:
        logger.error(f"Error loading game state for user {username}: {str(e)}")
        return None

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    if username not in active_connections:
        active_connections[username] = websocket
    
    # Send connection confirmation
    await websocket.send_json({"type": "connection_status", "message": "WebSocket connected"})
    
    try:
        # Try to load existing game state
        existing_game = load_game_state(username)
        if existing_game:
            games[username] = existing_game
            await websocket.send_json({"type": "game_restored", "message": "Existing game restored"})
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.debug(f"Received message from {username}: {message}")
            
            if message['type'] == 'create_and_start_game':
                game = OneNightWerewolf(num_players=message['num_players'], has_human=True, websocket=websocket)
                games[username] = game
                save_game_state(username, game)
                await asyncio.create_task(play_game(game, username))
            
            elif message['type'] == 'player_action':
                # Handle player actions (night actions, speaking, voting)
                game = games[username]
                player = next(p for p in game.players if p.name == message['player'])
                result = await player.handle_action(message['action'], game.game_state)
                await websocket.send_json({'type': 'action_result', 'player': player.name, 'result': result})
                save_game_state(username, game)
            
            else:
                await websocket.send_json(message)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {username}")
        del active_connections[username]
    except Exception as e:
        logger.error(f"Error in websocket connection for user {username}: {str(e)}")
    finally:
        if username in active_connections:
            del active_connections[username]
        if username in games:
            save_game_state(username, games[username])
            del games[username]

async def play_game(game, username):
    try:
        await game.play_game()
    finally:
        if username in games:
            save_game_state(username, games[username])
            del games[username]

async def broadcast(username: str, message: dict):
    if username in active_connections:
        await active_connections[username].send_text(json.dumps(message))

# Add a new route for testing
@app.get("/test")
async def endpoint_test():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
