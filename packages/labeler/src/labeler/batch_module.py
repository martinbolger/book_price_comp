from dataclasses import dataclass
from typing import List

from xai_sdk import Client
from xai_sdk.chat import Optional, system, user, image
from xai_sdk.tools import web_search

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


@dataclass
class BatchItemResult:
    batch_request_id: str
    response_text: Optional[str]
    is_success: bool
    error_message: Optional[str] = None


class Label_Batch:
    def __init__(self, client: Client = None, model: str = "grok-4.3"):
        self.client = client if client is not None else Client()
        self.model = model

    def create_batch(self, name: str) -> str:
        """Creates a new batch with the given name."""
        raise NotImplementedError("This method should be implemented in a subclass.")

    def add_request_to_batch(
        self,
        message: str,
        image_url: str,
        batch_request_id: str,
        system_prompt: str = None,
    ) -> object:
        """Adds a new request to the batch with the given message."""
        raise NotImplementedError("This method should be implemented in a subclass.")

    def run_batch(self, batch_id: str = None, batch_requests: list[object] = None):
        """Run the labeling process for the given batch request payloads."""
        raise NotImplementedError("This method should be implemented in a subclass.")

    def get_batch_results(self, batch_id: str) -> List[BatchItemResult]:
        """Fetches batch results and returns normalized BatchItemResult list."""
        raise NotImplementedError("This method should be implemented in a subclass.")


class XAI_Batch(Label_Batch):
    def __init__(self, client: Client = None, model: str = "grok-4.3"):
        self.client = client if client is not None else Client()
        self.model = model

    def create_batch(self, name: str) -> str:
        """Creates a new batch with the given name using the XAI SDK."""
        batch = self.client.batch.create(batch_name=name)
        print(f"Created batch: {batch.batch_id}")
        return batch.batch_id

    def add_request_to_batch(
        self,
        message: str,
        image_url: str,
        batch_request_id: str,
        system_prompt: str = None,
    ) -> object:
        """Adds a new request to the batch with the given message."""
        chat = self.client.chat.create(
            model=self.model,
            batch_request_id=batch_request_id,
            tools=[web_search()],
        )
        if system_prompt:
            chat.append(system(system_prompt))
        chat.append(user(message, image(image_url, detail="low")))
        return chat

    def run_batch(self, batch_id: str = None, batch_requests: list[object] = None):
        """Run the labeling process for the given batch request payloads."""
        # Get the list of chat objects from the dictionaries in batch_request_objs.
        self.client.batch.add(batch_id=batch_id, batch_requests=batch_requests)

    def _list_batch_results(
        self, batch_id: str, limit: int = 100, pagination_token: str = None
    ):
        """List the results of a batch with pagination support."""
        # Paginate through all results
        all_succeeded = []
        all_failed = []
        pagination_token = None
        while True:
            # Fetch a page of results (limit controls page size)
            page = self.client.batch.list_batch_results(
                batch_id=batch_id,
                limit=limit,
                pagination_token=pagination_token,
            )

            # Collect results from this page
            all_succeeded.extend(page.succeeded)
            all_failed.extend(page.failed)

            # Check if there are more pages
            if page.pagination_token is None:
                break
            pagination_token = page.pagination_token
        return all_succeeded, all_failed

    @staticmethod
    def extract_title_from_proto(result) -> str:
        """
        Parses native protobuf response from xAI Batch API,
        handling multi-turn tool executions cleanly.
        """
        comp_resp = getattr(result.response, "completion_response", None)
        if not comp_resp:
            return ""

        outputs = getattr(comp_resp, "outputs", [])

        # Iterate backwards through outputs to catch the final assistant answer
        for output in reversed(outputs):
            msg = getattr(output, "message", None)
            if not msg:
                continue

            content = getattr(msg, "content", "")

            # If finish_reason is REASON_STOP or content exists, return it
            if content and content.strip():
                return content.strip()

        return ""

    def get_batch_results(self, batch_id: str) -> List[BatchItemResult]:
        """Fetches batch results from xAI and returns normalized BatchItemResult list."""
        succeeded, failed = self._list_batch_results(batch_id)
        results: List[BatchItemResult] = []

        # Parse succeeded items
        for result in succeeded:
            rid = result.batch_request_id
            resp = result.proto.response

            if resp.HasField("completion_response"):
                # Chat completion response
                print(f"[{rid}] {result.response.content}")
                print(f"  Tokens used: {result.response.usage.total_tokens}")

            results.append(
                BatchItemResult(
                    batch_request_id=result.batch_request_id,
                    response_text=(result.response.content),
                    is_success=True,
                )
            )

        # Parse failed items
        for result in failed:
            results.append(
                BatchItemResult(
                    batch_request_id=result.batch_request_id,
                    response_text=None,
                    is_success=False,
                    error_message=getattr(result, "error", "Unknown batch error"),
                )
            )

        return results
