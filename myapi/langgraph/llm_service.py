from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config import settings


class FlashLLMService:
    def __init__(self):
        self.model = ChatGroq(
            api_key=settings.groq_api_key.get_secret_value(),
            model="openai/gpt-oss-20b",
            temperature=0.0,
        )

    def invoke(self, messages):
        return self.model.invoke(messages)

    def with_structured_output(self, schema):
        return self.model.with_structured_output(schema)


class ProLLMService:
    def __init__(self):
        self.model = ChatGroq(
            api_key=settings.groq_api_key.get_secret_value(),
            model="llama-3.3-70b-versatile",
            temperature=0.5,
        )

    def invoke(self, messages):
        return self.model.invoke(messages)

    def with_structured_output(self, schema):
        return self.model.with_structured_output(schema)


class ScoreLLMService:
    def __init__(self):
        self.model = ChatGroq(
            api_key=settings.groq_api_key.get_secret_value(),
            model="openai/gpt-oss-20b",
            temperature=0.0,
        )

    def invoke(self, messages):
        return self.model.invoke(messages)

    def with_structured_output(self, schema):
        return self.model.with_structured_output(schema)
    
