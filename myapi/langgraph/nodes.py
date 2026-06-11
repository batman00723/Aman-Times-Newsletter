from .state import NewsLetterState
from myapi.utilities.websearch import WebSearch
import asyncio
import json
from jinja2 import Template
from backend.config import settings
from myapi.models import Subscriber
import requests
import resend
from myapi.models import Subscriber
from backend.config import settings  
import time
import requests
import trafilatura
from .schemas import ScoredNewsResponse, CritiqueNodeResponse
import sib_api_v3_sdk
import re
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
        You are an expert Geopolitical Analyst specializing in India's strategic interests.

        Rate each news story from 1-10 based on BOTH:

        1. Impact on the global world order
        2. Strategic importance to India

        PRIORITIZE:
        - India's foreign policy
        - India's energy security
        - India's defense and military posture
        - India-China relations
        - India-Pakistan relations
        - India-US relations
        - BRICS
        - QUAD
        - Indian Ocean security
        - Trade corridors affecting India
        - Supply chains affecting India
        - Major geopolitical developments that directly or indirectly impact India

        Score based ONLY on evidence present in the article.

        SCORING RUBRIC:

        10:
        - Major geopolitical event directly affecting India's security, economy, diplomacy, or strategic position
        - Large-scale military conflict involving India's key partners or adversaries
        - Major disruption to energy supplies, shipping lanes, or trade routes affecting India

        8-9:
        - Significant regional shifts involving India
        - Major defense agreements
        - Strategic energy deals
        - Important sanctions, alliances, or diplomatic developments affecting India

        6-7:
        - Notable geopolitical developments with moderate implications for India
        - Regional diplomatic disputes
        - Elections or policy changes with potential strategic impact

        1-5:
        - General international news
        - Local political developments with little relevance to India
        - Human-interest stories
        - Domestic events with no geopolitical significance

        RULES:
        - Prefer India-relevant stories over equally important non-India stories.
        - Select 5 stories.
        - Exclude stories scoring below 6.


    NEWS STORIES:
    {json.dumps(news_feed)}
    """

    try: 
        structured_llm = llm.with_structured_output(ScoredNewsResponse)
        print("NEWS COUNT:", len(news_feed))
        print("PROMPT LENGTH:", len(prompt))
        
        response = structured_llm.invoke(prompt)
        print(f"Score Node Response: {response}")

        scored_items = response.articles
        filtered = [
            item for item in scored_items
            if item.score > 5
        ]

        filtered = sorted(
            filtered,
            key=lambda x: x.score,
            reverse=True
        )

        filtered = filtered[:5]

        # Here we map id to orignal search_results
        top_links= []
        for item in filtered:
            orignal_article= state['search_results'][item.id]
            top_links.append({
                "title": orignal_article["title"],
                "url": orignal_article["url"],
                "score": item.score,
                "reason": item.reason
            })
        
        print (f"Success: Selected {len(top_links)} high impact news")

        return {
            "top_links": top_links,
        }
    
    except Exception as e:
        print (f"Error Handling scoring node: {str(e)}")
        return {"logs": [f"Scoring Error: {str(e)}"]}
    

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

           Return ONLY the newsletter content.

            Do NOT explain your reasoning.
            Do NOT show your analysis.
            Do NOT show planning steps.
            Do NOT include any text before TODAY'S TRIGGER.

            CRITICAL OUTPUT RULE:
            Do not output <think> tags.
            Do not reveal reasoning.
            Do not reveal planning.
            Return only the final newsletter HTML.

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

        # print("RAW RESPONSE:")
        # print(response)
        # print("CONTENT:")
        # print(response.content)

        if hasattr(response, 'content') and isinstance(response.content, list):
            raw_text = response.content[0].get('text', '')
        else:
            raw_text = response.content
        
                

        raw_text = re.sub(
            r"<think>.*?</think>",
            "",
            response.content,
            flags=re.DOTALL
        ).strip()
        
        
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
    
    source_context = "\n\n".join(
    state["raw_markdown"]
    )
    
    prompt = f"""
        You are a Fact-Checker. Compare the Newsletter against the Source Markdown.
        
        SOURCE MARKDOWN:
        {source_context[:2000]}

        GENERATED NEWSLETTER:
        {state['newsletter']}

        You are a FINAL QUALITY GATE, not an editor.

        Your job is NOT to improve the newsletter.

        Your job is ONLY to prevent publication of newsletters containing:

        1. Clear factual hallucinations.
        2. Major factual inaccuracies.
        3. Serious omissions of one of the selected stories.
        4. Broken formatting.

        IMPORTANT:

        - Do NOT suggest stylistic improvements.
        - Do NOT suggest additional context.
        - Do NOT request deeper analysis.
        - Do NOT request more details.
        - Do NOT critique writing quality.
        - Do NOT critique structure.
        - Do NOT critique optional omissions.

        If the newsletter is factually correct and reasonably covers the selected stories, return:

        status = "publish"

        Only return:

        status = "revise"

        when a real factual issue would mislead the reader.

        DEFAULT DECISION: publish.
        Choose revise only if there is a clear factual error,
        hallucination, or omission of a selected story.

        If status = publish,
        critique must be an empty list.

        If uncertain, choose publish.

        """    
            
    structured_llm = llm.with_structured_output(CritiqueNodeResponse)
    start = time.time()

    try:
        response = structured_llm.invoke(prompt)
    except Exception:
        return {"status": "publish"}
    
    print(
    f"Reflection LLM time: {time.time()-start:.2f}s"
        )

    print(response)

    if response.status == "publish":
        return {"status": "publish"}
    else:
        issues = response.critique
        return {
            "status": "revise",
            "critique": issues,
            "iteration_count": state["iteration_count"] + 1
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


configuration = sib_api_v3_sdk.Configuration()
configuration.api_key["api-key"] = settings.brevo_api_key.get_secret_value()

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
    sib_api_v3_sdk.ApiClient(configuration)
)

def send_email_node(state: NewsLetterState):
    print("Node: Sending Newsletter")

    def get_recipient_list():
        return list(
            Subscriber.objects.filter(is_active=True)
            .values_list("email", flat=True)
        )

    recipients = get_recipient_list()

    if not state["newsletter"]:
        return {
            "status": "error",
            "logs": ["Newsletter content is empty"]
        }

    try:
        bcc_emails = [
            {"email": email}
            for email in recipients
        ]

        email = sib_api_v3_sdk.SendSmtpEmail(
            sender={
                "name": "Geopolitics Digest",
                "email": "batmanmishra23@gmail.com"
            },
            to=[
                {
                    "email": "batmanmishra23@gmail.com"
                }
            ],
            bcc=bcc_emails,
            subject="Geopolitics Digest Daily: Morning Briefing",
            html_content=state["newsletter"]
        )

        response = api_instance.send_transac_email(email)

        print(f"Newsletter sent: {response}")

        return {
            "status": "published"
        }

    except Exception as e:
        error_msg = f"Email not sent: {str(e)}"
        print(error_msg)

        return {
            "status": "error",
            "logs": [error_msg],
        }