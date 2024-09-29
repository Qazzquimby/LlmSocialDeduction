import asyncio
from playwright.async_api import async_playwright

async def websocket_connection_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Navigate to the frontend
        await page.goto("http://localhost:5173")
        
        # Wait for the WebSocket connection to be established
        await page.wait_for_selector("text=WebSocket connected")
        
        # Test creating a game
        await page.click("text=Create Game")
        await page.wait_for_selector("text=Game created")
        
        # Test starting a game
        await page.click("text=Start Game")
        await page.wait_for_selector("text=Game started")
        
        # Test night phase completion
        await page.wait_for_selector("text=Night phase completed")
        
        # Test day phase completion
        await page.wait_for_selector("text=Day phase completed")
        
        # Test voting completion
        await page.wait_for_selector("text=Voting completed")
        
        # Test game end
        await page.wait_for_selector("text=Game ended")
        
        await browser.close()

asyncio.run(websocket_connection_test())
import asyncio
import pytest
from fastapi.testclient import TestClient
from back.app import app, get_server_state
from back.websocket_management import websocket_manager

@pytest.fixture
def test_app():
    return TestClient(app)

@pytest.mark.asyncio
async def test_game_flow():
    # This is a basic structure for an integration test
    # You'll need to expand this based on your specific game flow
    client = TestClient(app)
    
    # Start a game
    response = client.post("/start_game", json={"name": "TestPlayer", "api_key": "test_key"})
    assert response.status_code == 200
    game_id = response.json()["gameId"]

    # Connect to WebSocket
    with client.websocket_connect(f"/ws/TestPlayer?api_key=test_key") as websocket:
        # Wait for game to start
        data = websocket.receive_json()
        assert data["type"] == "game_started"

        # Simulate game actions
        # You'll need to add more assertions and actions based on your game flow
        websocket.send_json({"type": "player_action", "action": "speak", "message": "Hello"})

        # Wait for game to end
        while True:
            data = websocket.receive_json()
            if data["type"] == "game_ended":
                break

    # Assert final game state
    # Add assertions based on your expected game outcome

# Add more test cases as needed

if __name__ == "__main__":
    pytest.main([__file__])
