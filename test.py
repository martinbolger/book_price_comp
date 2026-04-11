from google import genai

client = genai.Client(api_key="AIzaSyAZ2wGqsdUolxcSaNP2G7jUCFWMXWAWPRE")

for model in client.models.list():
    print(model.name)
