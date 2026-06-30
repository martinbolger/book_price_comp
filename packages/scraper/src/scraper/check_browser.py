import os
import sys
import subprocess

# Automatically ensure browsers exist before scraping
playwright_cache = os.path.expanduser("~/.cache/ms-playwright")
if not os.path.exists(playwright_cache) or not os.listdir(playwright_cache):
    print("📥 Playwright browsers missing. Installing...")
    subprocess.run([sys.executable, "-m", "playwright", "install"])
