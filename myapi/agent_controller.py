from ninja_extra import ControllerBase, api_controller, http_get, throttle
from ninja_extra.throttling import throttle, UserRateThrottle
from backend.config import settings
from ninja_extra import http_get, http_post, http_delete
from myapi.langgraph.llm_service import FlashLLMService, ProLLMService, ScoreLLMService
from myapi.langgraph.graph import create_newsletter_agent
import logging
from datetime import date
from .models import Subscriber
from .schemas import EmailSchema
from django.shortcuts import get_object_or_404

# Initialising them here not in init cus if i do it in itnit so everytime i hit exceute it runs so load on cpu
flash_service = FlashLLMService()
#pro_service = ProLLMService()
score_service= ScoreLLMService()
newsletter_agent = create_newsletter_agent(score_llm= score_service,
                                           flash_llm= flash_service
                                        )


@api_controller("/subscriber", tags= ['Subscribers'])
class EmailRecipentsOperationController(ControllerBase):

    @http_post("/add_subscriber")
    def subscribe(self, request, data: EmailSchema):
        subscriber= Subscriber.objects.create(email= data.email)
        subscriber.is_active= True
        subscriber.save()
        return {"message": "Successfully Subscribed to Geopolitical Newsletter"}
    
    @http_delete("/uncubscribe")
    def unsubscribe(self, request, data: EmailSchema):
        subscriber= get_object_or_404(Subscriber, email= data.email)
        subscriber.is_active= False
        subscriber.save()
        return {"message": "Unsubscibed to Geopolitical Newsletter,"
                "You can join back anytime."
                "You are always Welcomed."}

@api_controller("/agent", tags= ['Newsletter Agent'])
class AgentOperationController(ControllerBase):

    @http_get("/newsletter")
    #@throttle(UserRateThrottle)
    def get_newsletter(self, request):
        print("starting to call newsletter agent")

        today = date.today().isoformat()
        session_id = f"{today}-aman"
        
        config= {"configurable": {"thread_id": session_id}}

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

        try: 
            final_state= newsletter_agent.invoke(initial_state, config= config)
            print("Newsletter Generated.")

            newsletter_preview= final_state.get("newsletter", "Empty")

            return {
                "newsletter_preview": newsletter_preview,
                "session_id": session_id,
                "logs": final_state.get("logs", [])
            }
        
        except Exception as e:
            logger= logging.getLogger(__name__)
            logger.error(f"Agent Execution Error: {str(e)}", exc_info= True)

            return {
                "message": "There is problem while running newsletter Agent",
                "deatils": str(e) if settings.debug else "Internal Server Error"
            }
        

