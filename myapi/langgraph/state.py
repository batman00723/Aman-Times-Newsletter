from typing import TypedDict, Annotated
import operator

class NewsLetterState(TypedDict):
    query: str
    search_results: list[dict]
    top_links: list[dict]
    raw_markdown: list[str]
    newsletter: str
    iteration_count: int
    critique: Annotated[list[str], operator.add] 
    status: str
    logs: Annotated[list[str], operator.add]     
