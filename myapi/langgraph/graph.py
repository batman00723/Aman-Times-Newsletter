from langgraph.graph import StateGraph, END
from functools import partial
from .state import NewsLetterState
from backend.config import settings
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import MemorySaver
from myapi.langgraph.nodes import search_node, scoring_node, crawl_node, newsletter_generator_node, reflection_node, send_email_node, should_continue

DB_URL = settings.db_url.get_secret_value()

_pool = ConnectionPool(
    conninfo=DB_URL,
    max_size=10,
    kwargs={"autocommit": True, "prepare_threshold": 0} 
)

memory = PostgresSaver(_pool)
memory.setup()

def create_newsletter_agent(score_llm, flash_llm):
    workflow= StateGraph(NewsLetterState)

    workflow.add_node("search", search_node)
    workflow.add_node("score", partial(scoring_node, llm= score_llm))
    workflow.add_node("crawl", crawl_node)
    workflow.add_node("generate", partial(newsletter_generator_node, llm= flash_llm))
    workflow.add_node("reflect", partial(reflection_node, llm= flash_llm))
    workflow.add_node("publish", send_email_node)

    workflow.set_entry_point("search")
    
    workflow.add_edge("search", "score")
    workflow.add_edge("score", "crawl")
    workflow.add_edge("crawl", "generate")
    workflow.add_edge("generate", "reflect")
    
    workflow.add_conditional_edges(
        "reflect",
        should_continue,
        {
            "revise": "generate", # if should_continue function retuirns "revise" thrn loop back
            "end": "publish"      # if it returns "end" then go to "publish" node
        }
    )

    workflow.add_edge("publish", END)

    return workflow.compile(checkpointer= memory)