from .state import NewsLetterState
from myapi.utilities.websearch import WebSearch
import asyncio
import json
from jinja2 import Template
from django.core.mail import EmailMessage, get_connection
from backend.config import settings
from myapi.models import Subscriber
import trafilatura
import requests
#from .tasks import send_newsletter_task

def search_node(state: NewsLetterState):
    """Takes optimised query and finds job links on the web"""
    query = state["query"]
    
    print(f"Searching for: {query}")

    # Run the async search synchronously using a temporary loop
    try:
        # This forces the coroutine to finish and returns the actual list
        search_results = asyncio.run(WebSearch.search_the_web(query=query))

    except Exception as e:
        print(f"Search failed: {e}")
        return {"search_results": [], "logs": [f"Search Failure: {str(e)}"]}

    if isinstance(search_results, str): 
        return {"search_results": [], "logs": ["Web Search Error"]}



    return {
        "search_results": search_results
    }

def scoring_node(state: NewsLetterState, llm):
    print("Node: Scoring News")

    if not state['search_results']:
        return {"logs": ["Scoring failed: No serach results found."]}
    
    # Sending title and snippet to llm for deduplication scoring
    news_feed= []
    for i, item in enumerate(state['search_results']):
        news_feed.append({
            "id": i,
            "title": item.get("title"),
            "snippet": item.get("content", "")[:500] # sending only limited context
        })

    prompt = f"""
    You are an expert Geopolitical Analyst. 
    YOU ARE A POLARISING AND BLUNT GEOPOLITICS NEWS ANALYST.
    Rate each news story below from 1 to 10 based on its importance to the global world order. 
    
    Score based ONLY on:
    - presence of conflict, sanctions, military movement
    - involvement of major economies or alliances
    - measurable impact on trade, energy, or diplomacy

    Do NOT infer importance without evidence

    SCORING RUBRIC:
    - 10: Potential global conflict, major regime change in a nuclear power, or collapse of a major global economy related to India or directly or inderectly affecting India.
    - 8: Significant regional shifts, major energy/trade treaty signing, or high-level international sanctions.
    - 6-7: Routine diplomatic friction, local elections with minor regional impact.
    - <5: General news, human interest, or local crime.

    RULES:
    - Only return stories with a score GREATER than 5.
    - Select a MAXIMUM of 4 stories and atleast 3 stories.
    - Return ONLY valid JSON.
    
    FORMAT:
    [
      {{"id": 0, "score": 9, "reason": "concise reason why this is high impact"}}
    ]

    NEWS STORIES:
    {json.dumps(news_feed)}
    """

    try: 
        response= llm.invoke(prompt).content
        

        raw_json = response.replace("```json", "").replace("```", "").strip()
        scored_items = json.loads(raw_json)
 

        # Heer we map id to orignal search_results
        top_links= []
        for item in scored_items:
            try: 
                orignal_article= state['search_results'][item["id"]]
                top_links.append({
                    "title": orignal_article["title"],
                    "url": orignal_article["url"],
                    "score": item["score"],
                    "reason": item["reason"]
                })
            except (KeyError, IndexError):
                continue
        
        print (f"Success: Selected {len(top_links)} high impact news")
        return {
            "top_links": top_links,
        }
    
    except Exception as e:
        print (f"Error Handling scoring node: {str(e)}")
        return {"logs": [f"Scoring Error: {str(e)}"]}
    

import time
import requests
import trafilatura

def crawl_node(state: NewsLetterState):
    print("Node: Crawling content")

    if not state.get('top_links'):
        return {"logs": ["Crawl failed: No top links available"]}

    urls = [link['url'] for link in state["top_links"]]
    extracted_text = []

    START_TIME = time.time()
    MAX_TOTAL_TIME = 10  # seconds
    REQUEST_TIMEOUT = 3  # per request

    for url in urls:

        if time.time() - START_TIME > MAX_TOTAL_TIME:
            print("Crawl time budget exceeded, stopping early")
            break

        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT, headers={
                "User-Agent": "Mozilla/5.0"
            })

            if response.status_code != 200:
                continue

            html = response.text

            if html and len(html) < 2_000_000:
                text = trafilatura.extract(
                    html,
                    include_comments=False,
                    include_tables=False,
                    no_fallback=False,
                    include_images=False,
                )

                if text:
                    extracted_text.append(text[:4000])

        except Exception as e:
            print(f"Failed {url}: {e}")
            continue

    if not extracted_text:
        return {"raw_markdown": [], "logs": ["No context extracted"]}

    return {"raw_markdown": extracted_text}


def newsletter_generator_node(state: NewsLetterState, llm):

    current_iter = state["iteration_count"] + 1
    print(f"Node: Generating Newsletter (Iterattion --{current_iter}--)")
    template_path= "newsletter_template.html"
    try: 
        with open(template_path, "r", encoding= "utf-8") as f:
            template_str= f.read()
    except FileNotFoundError:
        return {"logs": ["Template file not found in root."]}
    
    context= "\n\n---\n\n".join(state["raw_markdown"])

    full_critique_history = "\n".join([f"- {c}" for c in state["critique"]])
    critique_section = f"\nPAST ERRORS TO FIX:\n{full_critique_history}" if state["critique"] else ""

    prompt = f""" 
        Write 4-5 professional bullet points based on the SOURCE FACTS.

        Every claim must:
        - reference a specific actor (country/org)
        - include a concrete action
        - avoid vague phrases like "global powers", "significant shift", "global implications"

        FOR EXAMPLE: “If Hormuz disruption continues, India benefits short-term via discounted oil,
        but faces long-term shipping risk.”

        STRUCTURE:
        
        1. TODAY’S TRIGGER (H3 Header):
           Summarize the most volatile event in 1-2 sentences.
            - Must include:
            - Actor (country/org)
            - Action (what happened)
            - No vague language

        2. KEY SHIFTS (3-4 high-density bullets):
           - Each <li> must start with a **BOLD TITLE** representing the core shift.
           - Follow with 2 sentences of 'The Impact' (why it matters).
           - End with an *Italicized Forward Signal* (what to watch for next).
           - Include (Source: Name) at the end of every bullet like  like (Source: Reuters, IEA report)

        3. FORMATTING:
           - Use HTML tags: <h3>, <ul>, <li>, <b>, <i>.
           - No markdown (no # or * for bold). Use tags only.

        SOURCE FACTS:
        {context}

        STYLE:
        - Blunt, executive, and sophisticated geopolitical analyst.
        - Format as an HTML unordered list: <ul><li>...</li></ul>.
        - Each bullet should be 3-4 lines of deep analysis.
        
        {f"CRITIQUE TO FIX: {critique_section}"}
        """
    try:
        response = llm.invoke(prompt)

        if hasattr(response, 'content') and isinstance(response.content, list):
            raw_text = response.content[0].get('text', '')
        else:
            raw_text = response.content
        
        
        clean_text = raw_text.replace('\\n', '\n').strip()

        # jinja is used to bake text into html
        jinja_template= Template(template_str)
        final_html= jinja_template.render(newsletter_content= clean_text)

        return {
            "newsletter": final_html,
            "iteration_count": current_iter
        }
    
    except Exception as e:
        return {"logs": [f"Generator Error: {str(e)}"]}
    

def reflection_node(state: NewsLetterState, llm):
    print("Node: Reflecting on Quality")

    if state["iteration_count"]>=2:
        print ("Max iterations reached. moving to publish with logs")
        return {"status": "publish"}
    
    prompt = f"""
        You are a Fact-Checker. Compare the Newsletter against the Source Markdown.
        
        SOURCE MARKDOWN:
        {state['raw_markdown']}

        GENERATED NEWSLETTER:
        {state['newsletter']}

        CHECK FOR:
        1. Hallucinations (Facts not in source).
        2. Missing major news from the top 6 links.
        3. Formatting errors.

        If the newsletter is accurate, you must only return "PUBLISH".
        If there are errors, return a detailed list of what to fix.

        IMPORTANT: Return ONLY JSON:

        {{"status": "publish"}}

        OR

        {{"status": "revise", "issues": ["..."]}}
        """    
            
    response = llm.invoke(prompt).content

    res_str = str(response[0]) if isinstance(response, list) else str(response)

    try:
        clean_json = res_str.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)

        if data.get("status") == "publish":
            return {"status": "publish"}
        else:
            issues = data.get("issues", ["No specific issues listed"])
            return {
                "status": "revise",
                "critique": issues 
            }

    except:
        return {
            "status": "sending",
            "critique": ["Invalid JSON from reflection"],
            "iteration_count": state['iteration_count'] + 1
        }
    

        
def should_continue(state: NewsLetterState):
    """
    Router function to decide whether to loop back for a revision 
    or proceed to the final publication.
    """
    print(f"--- [ROUTER]: Checking State | Status: {state['status']} | Iterations: {state['iteration_count']} ---")
    if state['status'] == "publish":
        return "end"

    if state['iteration_count'] >= 2:
        return "end"
    if state['status'] == "revise":
        print("--- [ROUTER]: Revision required. Looping back to Generate. ---")
        return "revise"
    
    return "end"


# ---- FOR DEPLOYMENT NO BACKGROUND WORKERS AS RENDER RAILWAY DO NOT HAVE FREE TIER FOR BACKGROUND WORKERS ----

# def send_email_node(state: NewsLetterState):
#     print("Node: Offloading Newsletter to Celery Queue")

#     if not state.get('newsletter'):
#         return {"status": "error", "logs": ["Email failed: Newsletter content is empty"]}
    
#     # Query recipients synchronously within the node
#     recipients = list(Subscriber.objects.filter(is_active=True).values_list('email', flat=True))

#     send_newsletter_task.delay(state['newsletter'], recipients)

#     print("Task queued in Redis. Moving to end state.")
#     return {"status": "published"}  


def send_email_node(state: NewsLetterState):
    print("Node: Sending Newsletter")
    print(f"{state['newsletter']}")

    def get_recipient_list():
        return list(Subscriber.objects.filter(is_active=True).values_list('email', flat=True))

    recipients = get_recipient_list()
    if not state['newsletter']:
        return {"logs": ["Email failed: Newsletter content is empty"]}

    try:
        connection= get_connection(fail_silently= False)
        email = EmailMessage(
            subject="Geopolitics Digest Daily: Morning Briefing",
            body=state['newsletter'],
            from_email= settings.email_host_user,
            to= ["amanmishrarewa23@gmail.com"],  # my secondary email address specially for this work
            bcc= recipients, # using blind carbon copy for privacy as others cat see each others email address
            connection= connection  
        )
        email.content_subtype = "html"    

        print(f"Attempting to Send")    

        email.send()
        print("Newsletter Sent to Recipients")
        return {"status": "published"}

    except Exception as e:
        error_msg = f"Email not sent: {str(e)}"
        print(f"Error: {error_msg}")
        return {
            "status": "error",
            "logs": [error_msg],
        }