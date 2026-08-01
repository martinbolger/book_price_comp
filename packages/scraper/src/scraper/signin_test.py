from playwright.async_api import async_playwright
import asyncio


async def save_ebay_session():
    async with async_playwright() as p:
        # Launch browser with GUI
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.ebay.com/signin")
        print(
            "Please log in manually in the browser window, then press ENTER in terminal..."
        )
        input()

        # Save your logged-in browser state to a JSON file
        await context.storage_state(path="ebay_state.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(save_ebay_session())