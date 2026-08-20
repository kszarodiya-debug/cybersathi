"""Chat request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=2000)

    @field_validator("message")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("Message contains an invalid character.")
        return value


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str
    response: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]


class ClearChatResponse(BaseModel):
    deleted_count: int
