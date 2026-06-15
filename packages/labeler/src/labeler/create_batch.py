from xai_sdk import Client

def create_batch(name: str) -> Client.Batch:
    client = Client()

    # Create a batch with a descriptive name
    batch = client.batch.create(batch_name=name)

    print(f"Created batch: {batch.batch_id}")

    return batch
from xai_sdk import Client
from xai_sdk.chat import system, user
from xai_sdk.tools import web_search

def add_to_batch_requests(message: str, batch_id: str, batch_requests: list) -> list:
    client = Client()

    # Chat completion with tools
    chat = client.chat.create(
        model="grok-4.3",
        batch_request_id=batch_id,
        tools=[web_search()],
    )
    chat.append(system("You are a book labeler. You will be given a link to an image of a book and you need to find the name of the book in Japanese. If the book has multiple volumes, include the volume."))
    chat.append(user(message))
    batch_requests.append(chat)
    return batch_requests