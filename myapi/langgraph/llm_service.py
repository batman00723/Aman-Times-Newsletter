from backend.config import settings
from langchain_cerebras import ChatCerebras
from langchain_google_genai import ChatGoogleGenerativeAI

class FlashLLMService:
    def __init__(self):
        self.model= ChatGoogleGenerativeAI(
            api_key= settings.google_api_key.get_secret_value(),
            model= "gemini-3.1-flash-lite-preview",
            temperature= 0.0
        )
    def invoke(self, messages):
        response= self.model.invoke(messages)
        return response
    
    
class ProLLMService:
    def __init__(self):
        self.model= ChatGoogleGenerativeAI(
            api_key= settings.google_api_key.get_secret_value(),
            model= "gemini-3.1-pro-preview",
            temperature= 0.7
        )
    def invoke(self, messages):
        response= self.model.invoke(messages)
        return response
    
class ScoreLLMService:
    def __init__(self):
        self.model= ChatCerebras(
            api_key= settings.cerebras_api_key.get_secret_value(),
            model= "llama3.1-8b",
            temperature= 0.0
        )
    def invoke(self, messages):
        response= self.model.invoke(messages)
        return response
    
    
