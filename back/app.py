import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from games.one_night_ultimate_werewolf.game import OneNightWerewolf
import asyncio

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

@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await websocket.accept()
    if game_id not in active_connections:
        active_connections[game_id] = []
    active_connections[game_id].append(websocket)
    
    # Send connection confirmation
    await websocket.send_json({"type": "connection_status", "message": "WebSocket connected"})
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['type'] == 'create_game':
                games[game_id] = OneNightWerewolf(num_players=message['num_players'], has_human=True, websocket=websocket)
                await websocket.send_json({'type': 'game_created', 'game_id': game_id})
            
            elif message['type'] == 'start_game':
                game = games[game_id]
                asyncio.create_task(play_game(game, game_id))
            
            elif message['type'] == 'player_action':
                # Handle player actions (night actions, speaking, voting)
                game = games[game_id]
                player = next(p for p in game.players if p.name == message['player'])
                result = await player.handle_action(message['action'], game.game_state)
                await websocket.send_json({'type': 'action_result', 'player': player.name, 'result': result})
            
            else:
                await websocket.send_json(message)
    
    except WebSocketDisconnect:
        active_connections[game_id].remove(websocket)

async def play_game(game, game_id):
    await game.play_game()
    del games[game_id]

async def broadcast(game_id: str, message: dict):
    for connection in active_connections[game_id]:
        await connection.send_text(json.dumps(message))

# Add a new route for testing
@app.get("/test")
async def endpoint_test():
    return {"status": "ok"}

# Add a new route for testing
@app.get("/test")
async def endpoint_test():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
