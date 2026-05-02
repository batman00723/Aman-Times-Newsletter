# Geopolitical Newsletter Agent

An autonomous, self-correcting AI agent that researches, scores, and delivers geopolitical briefings. Built with **LangGraph** for agentic orchestration and **Django Ninja** for backend.

   ## Problem
   Manually researching news takes more than an hour daily.
   
   ## Solution
   LangGraph agentic workflow that:
   - Scrapes multiple sources
   - Analyzes & critiques content
   - Generates an HTML newsletter and sends it to your Mail

## 🚀 Performance Optimization

This system was iteratively optimized using LangSmith tracing to identify and eliminate bottlenecks.

### Before Optimization
- End-to-end latency: ~95–120s (P50)
- Tail latency: ~180s (P99)
- Crawl step: ~60s (browser-based scraping)
- Token usage: ~40k per run

### After Optimization
- End-to-end latency: ~24s (P50)
- Tail latency: ~30s (P99)
- Crawl step: ~4–8s (parallel HTTP + trafilatura)
- Token usage: <20k per run

### Key Improvements
- Replaced browser-based (Crawl4AI) scraping with lightweight HTTP parsing (trafilatura)
- Parallelized ingestion using async execution
- Reduced redundant LLM context → lower token cost
- Offloaded email delivery via Celery + Redis (non-blocking execution)

> Result: ~75% latency reduction and ~6x improvement in tail latency (P99)

### Architecture

<p align="center">
  <img src="Newsletter Agent Final1.png" width="600" title="System Architecture">
</p>

1. **Search & Discovery**: Dynamically queries real-time news via Tavily, focusing on trade, conflict, and energy security.
2. **Impact Scoring**: An LLM-based filter that scores news (1-10) to eliminate noise and select the top 6 high-impact stories.
3. **Async Crawling**: Uses `trafilatura` to extract clean content for LLM.
4. **Editorial Generation**: Bakes raw data into a professional HTML template using Jinja2.
5. **Quality Reflection**: A dedicated node that checks for hallucinations or formatting errors. If "revise" is triggered, the agent loops back to re-draft the newsletter.

---

## Tech Stack
- **Framework**: Django Ninja (FastAPI-style performance with Django robustness)
- **Agent Orchestration**: LangGraph (Stateful, multi-step workflows)
- **LLMs**: Gemini 3.1 Flash for Generation and llama3.1-8b by Cerebras for Scoring Node.
- **Data Fetching**: Trafilatura & Tavily Search API
- **State Management**: Pydantic v2 & Postgres Checkpointing
- **Background Tasks**: Celery (Worker) and Redis (Queue) for Email Publish Offloading to further reduce User Percieved Latency.

---

## Technical Highlights
- **Agentic Loops**: Implemented a conditional router that manages state transitions.
- **State Persistence**: Used `PostgresSaver` for thread-based conversation history and state recovery.
- **Production Infrastructure**: Designed a secure API layer with Pydantic settings and SMTP integration for automated delivery.

---
