import asyncio
from datetime import date
from django.core.management.base import BaseCommand
from myapi.langgraph.graph import create_newsletter_agent

class Command(BaseCommand):
    help = 'Triggers the Newsletter Agent workflow via CLI'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- War Mode: Initializing Agent ---'))
        
        try:
           
            newsletter_agent = create_newsletter_agent() 
            
            # 2. Run the asynchronous execution
            asyncio.run(self.execute_agent(newsletter_agent))
            
            self.stdout.write(self.style.SUCCESS('--- Success: Newsletter Process Complete ---'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Deployment Error: {str(e)}"))
            exit(1)

    async def execute_agent(self, agent):
        today = date.today().isoformat()
        session_id = f"{today}-aman"
        config = {"configurable": {"thread_id": session_id}}

        # Matching your AgentOperationController state exactly
        initial_state = {
            "query": "Breaking geopolitical news in the last 24 hours affecting US, especially India, China, Russia, Europe or any major countries.",
            "search_results": [],
            "top_links": [],
            "raw_markdown": [],
            "newsletter": "",
            "iteration_count": 0,
            "status": "pending",
            "logs": []
        }

        # Using ainvoke for the async LangGraph workflow
        final_state = await agent.ainvoke(initial_state, config=config)
        
        # Log a snippet for verification in GitHub Actions
        preview = final_state.get("newsletter", "Empty")
        self.stdout.write(f"Newsletter Generated (Preview): {preview[:200]}...")