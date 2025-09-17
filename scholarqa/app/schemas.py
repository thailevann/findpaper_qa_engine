from typing import List, Optional, Dict, Any
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


# Enhanced schemas for ScholarQA pipeline with metadata and citations
class RankedPassage(BaseModel):
    paper_id: str
    title: str
    evidence: str
    cross_score: float
    final_score: float


class QuoteWithMetadata(BaseModel):
    quote_text: str
    paper_id: str
    title: str
    score: float
    similarity_score: float
    passage_index: int
    metadata: Dict[str, Any]


class SectionInfo(BaseModel):
    name: str
    description: str
    narrative: str
    quotes: List[QuoteWithMetadata]
    quote_count: int
    papers_referenced: List[str]


class ComparisonTable(BaseModel):
    section: str
    headers: List[str]
    rows: List[Dict[str, Any]]
    paper_count: int
    metadata: Dict[str, Any]


class ProcessingTrace(BaseModel):
    pipeline_start: bool = False
    query: str
    input_passages: int
    retrieved_passages: Optional[int] = None
    embeddings_generated: Optional[int] = None
    reranked_passages: Optional[int] = None
    extracted_quotes: Optional[int] = None
    outline_generated: Optional[bool] = None
    sections_created: Optional[int] = None
    comparison_tables: Optional[int] = None
    pipeline_completed: Optional[bool] = None
    final_sections: Optional[int] = None
    final_quotes: Optional[int] = None
    final_papers: Optional[int] = None
    error: Optional[str] = None
    pipeline_failed: Optional[bool] = None


class ReportMetadata(BaseModel):
    total_sections: int
    total_quotes: int
    total_papers: int
    comparison_tables_count: int


class StructuredReport(BaseModel):
    query: str
    summary: str
    sections: List[SectionInfo]
    comparison_tables: List[ComparisonTable]
    processing_trace: ProcessingTrace
    metadata: ReportMetadata


# Legacy schemas for backward compatibility
class QARequest(BaseModel):
    query: str
    ranked_passages: List[RankedPassage]
    model: Optional[str] = Field(default=None, description="OpenAI model name; uses env default if None")
    max_themes: int = Field(5, ge=1, le=12)


class QAResponse(BaseModel):
    query: str
    filtered_passages: List[str]
    themes: List[Theme]
    final_report: str
    processing_info: Dict[str, Any]


# New ScholarQA pipeline request/response schemas
class ScholarQARequest(BaseModel):
    query: str
    ranked_passages: List[RankedPassage]
    model: Optional[str] = Field(default=None, description="OpenAI model name; uses env default if None")
    retrieval_top_k: int = Field(50, ge=1, le=100, description="Number of passages to retrieve initially")
    rerank_top_k: int = Field(20, ge=1, le=50, description="Number of passages to keep after reranking")


class ScholarQAResponse(BaseModel):
    structured_report: StructuredReport
    success: bool
    error_message: Optional[str] = None


