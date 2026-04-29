# Geopolitical Insight Agent (Autonomous News Engine)

An autonomous, self-correcting AI agent that researches, scores, and delivers high-stakes geopolitical briefings. Built with **LangGraph** for agentic orchestration and **Django Ninja** for a high-performance backend.

### Core Architecture (LangGraph Nodes)

<p align="center">
  <img src="Newsletter Agent .png" width="600" title="System Architecture">
</p>

1. **Search & Discovery**: Dynamically queries real-time news via Tavily, focusing on trade, conflict, and energy security.
2. **Impact Scoring**: An LLM-based filter that scores news (1-10) to eliminate noise and select the top 6 high-impact stories.
3. **Async Crawling**: Uses `Crawl4AI` with a headless browser to extract clean Markdown from source URLs.
4. **Editorial Generation**: Bakes raw data into a professional HTML template using Jinja2.
5. **Quality Reflection**: A dedicated node that checks for hallucinations or formatting errors. If "revise" is triggered, the agent loops back to re-draft the newslettter.

---

## Tech Stack
- **Framework**: Django Ninja (FastAPI-style performance with Django robustness)
- **Agent Orchestration**: LangGraph (Stateful, multi-step workflows)
- **LLMs**: Gemini 1.5 Pro (Reasoning) & Gemini 1.5 Flash (Generation)
- **Data Fetching**: Crawl4AI & Tavily Search API
- **State Management**: Pydantic v2 & Postgres Checkpointing

---

## Technical Highlights
- **Agentic Loops**: Implemented a conditional router that manages state transitions based on quality scores.
- **Resilient Web Scraping**: Configured `Crawl4AI` to block heavy assets (images/ads) for 5x faster processing.
- **State Persistence**: Used `MemorySaver` for thread-based conversation history and state recovery.
- **Production Infrastructure**: Designed a secure API layer with Pydantic settings and SMTP integration for automated delivery.

---

## Installation & Setup

1. **Clone & Environment**:
   ```bash
   git clone [https://github.com/amanmishra23/geopolitical-newsletter-agent.git](https://github.com/amanmishra23/geopolitical-newsletter-agent.git)
   cd geopolitical-newsletter-agent
   python -m venv venv
   source venv/bin/activate  # venv\Scripts\activate on Windows
   pip install -r requirements.txt
