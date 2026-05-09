import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.google.com")
        print(f"Title: {await page.title()}")
        await page.screenshot(path="google.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())