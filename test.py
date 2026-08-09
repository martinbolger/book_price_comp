from datetime import date

from enum import Enum
from pydantic import BaseModel, Field


from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Book(BaseModel):
    # This ensures the schema stays simple
    model_config = ConfigDict(use_enum_values=True)

    is_book: bool = Field(..., description="Whether the item is a book or not")
    item_type: str = Field(
        ..., description="Type: book, magazine, manga_volume, set, or other"
    )
    title_jp: str = Field(..., description="Title in Japanese or 'n/a'")
    ISBN: str = Field(..., description="ISBN or 'n/a'")
    publisher_jp: str = Field(..., description="Publisher in Japanese or 'n/a'")
    cost_new_yen: float = Field(..., description="Cost new or 0", ge=0)
    cost_used_yen: float = Field(..., description="Cost used or 0", ge=0)
    extra_details: str = Field(..., description="Extra info or empty string")


with open("book_schema.json", "w") as f:
    f.write(str(Book.model_json_schema()))
