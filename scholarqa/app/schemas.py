from typing import List, Optional
from pydantic import BaseModel, Field


class EmbedRequest(BaseModel):
    text: str = Field(..., description="Input passage to embed")


class EmbedResponse(BaseModel):
    embedding: List[float]


class FilterQuotesRequest(BaseModel):
    query: str
    passages: List[str]
    top_k: int = Field(10, ge=1, le=1000, description="Number of passages to keep")


class FilterQuotesResponse(BaseModel):
    query: str
    filtered_passages: List[str]
    indices: List[int] = Field(..., description="Indices of the kept passages from the original list")
    scores: List[float] = Field(..., description="Cosine similarity scores aligned with indices")


class GenerateThemesRequest(BaseModel):
    query: str
    passages: List[str]
    model: Optional[str] = Field(default=None, description="OpenAI model name; uses env default if None")
    max_themes: int = Field(5, ge=1, le=12)


class Theme(BaseModel):
    name: str
    quotes: List[str]


class GenerateThemesResponse(BaseModel):
    themes: List[Theme]


class FinalReportRequest(BaseModel):
    query: str
    themes: List[Theme]
    model: Optional[str] = Field(default=None, description="OpenAI model name; uses env default if None")


class FinalReportResponse(BaseModel):
    report: str


