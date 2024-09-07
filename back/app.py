import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from games.one_night_ultimate_werewolf.game import OneNightWerewolf

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
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['type'] == 'create_game':
                games[game_id] = OneNightWerewolf(num_players=message['num_players'], has_human=True)
                await broadcast(game_id, {'type': 'game_created', 'game_id': game_id})
            
            elif message['type'] == 'start_game':
                game = games[game_id]
                game.setup_game()
                await broadcast(game_id, {'type': 'game_started', 'players': [p.name for p in game.players]})
                
                # Start night phase
                game.play_night_phase()
                await broadcast(game_id, {'type': 'night_phase_completed'})
                
                # Start day phase
                game.play_day_phase()
                await broadcast(game_id, {'type': 'day_phase_completed'})
                
                # Start voting phase
                executed_players = game.voting_phase()
                await broadcast(game_id, {'type': 'voting_completed', 'executed': [p.name for p in executed_players]})
                
                # Check win condition
                game.check_win_condition(executed_players)
                await broadcast(game_id, {'type': 'game_ended'})
            
            elif message['type'] == 'player_action':
                # Handle player actions (night actions, speaking, voting)
                game = games[game_id]
                player = next(p for p in game.players if p.name == message['player'])
                result = player.handle_action(message['action'], game.game_state)
                await broadcast(game_id, {'type': 'action_result', 'player': player.name, 'result': result})
            
            else:
                await broadcast(game_id, message)
    
    except WebSocketDisconnect:
        active_connections[game_id].remove(websocket)

async def broadcast(game_id: str, message: dict):
    for connection in active_connections[game_id]:
        await connection.send_text(json.dumps(message))

# Add a new route for testing
@app.get("/test")
async def test_endpoint():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
