from google import genai
import PIL.Image

# 1. Initialize the client (No more stateful 'GenerativeModel' objects)
client = genai.Client(api_key="AIzaSyAZ2wGqsdUolxcSaNP2G7jUCFWMXWAWPRE")

# 2. Load the image
img = PIL.Image.open("cover_test.jpg")

# 3. Generate content
# Note: The new SDK uses a flat list for contents; images can be passed directly.
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        "この本のタイトルとISBNを教えてください。",
        img,
    ],
)

print(response.text)
