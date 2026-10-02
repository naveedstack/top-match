from pydantic import BaseModel, Field


class Citation(BaseModel):
    claim: str
    quote: str


class ModelEvaluation(BaseModel):
    is_resume: bool
    refusal_reason: str | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    key_strengths: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    injection_suspected: bool = False


class EvaluationResult(BaseModel):
    is_resume: bool
    refusal_reason: str | None
    score: int | None
    key_strengths: list[str]
    missing_requirements: list[str]
    citations: list[Citation]
    injection_suspected: bool
    needs_review: bool
    citations_submitted: int
    model_name: str
    prompt_version: str
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None
