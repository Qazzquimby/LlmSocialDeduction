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
