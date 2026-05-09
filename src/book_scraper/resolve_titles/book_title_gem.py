from urllib import response
from google import genai
from google.genai import types
import requests
import os
import logging
import ollama
from sqlalchemy.orm import sessionmaker
import time

from book_scraper.database import get_engine, init_db
from book_scraper.models import BookEntry
from book_scraper.utils import hash_string

logging.basicConfig(level=logging.INFO)


def get_image_from_url(url: str):
    # 1. Download the image bytes into memory
    image_bytes = requests.get(url).content
    image = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

    return image


import httpx
import ollama


def identify_book_local(image_url: str):
    # 1. Fetch image from eBay
    headers = {"User-Agent": "Mozilla/5.0"}
    img_response = httpx.get(image_url, headers=headers)

    # 2. Send to Ollama (Ollama library handles the bytes)
    response = ollama.chat(
        model="llava-phi3",
        messages=[
            {
                "role": "user",
                "content": "What is the Title and Author of this book?",
                "images": [img_response.content],
            }
        ],
    )
    return response["message"]["content"]


def identify_book(image_url: str, client: genai.Client):
    img = get_image_from_url(image_url)

    # 3. Generate content
    # Note: The new SDK uses a flat list for contents; images can be passed directly.
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            "この本のフルタイトルを教えてください。このように答えてください：Title:<タイトル>",
            img,
        ],
    )
    logging.info(f"Title from Gemini for image {image_url}: {response.text}")
    return response.text


if __name__ == "__main__":
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    image_url = "https://i.ebayimg.com/images/g/F2MAAeSwgxZpu2ff/s-l500.webp"
    response = identify_book(image_url, client)
    print(response)
