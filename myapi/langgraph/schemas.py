from pydantic import BaseModel, Field
from typing import Literal


class ScoredNews(BaseModel):
    id: int = Field(description="News article id")
    score: int = Field(ge=1, le=10, description="Importance score from 1-10")
    reason: str = Field(description="Why this story matters geopolitically")

class ScoredNewsResponse(BaseModel):
    articles: list[ScoredNews]


class CritiqueNodeResponse(BaseModel):
    status: Literal["revise", "publish"] = Field(description= "Decision to publish or revise")
    critique:  list[str] = Field(default_factory=list, description= "List of reason to revise and what to revise")

