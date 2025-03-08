from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from context import AppContext

class LlmManager:
    """
    The LlmManager class serves as a retriever of the LLM that we are using

    It holds the logger which can be instantiated and called through the application
    """
    def __init__(self, app_context: AppContext):
        self.app_context = app_context

    @property
    def get_llm_instance(self) -> BaseChatModel:
        llm_configuration = self.app_context.configurations.llm

        return ChatOpenAI(
			openai_api_key=self.app_context.env_vars.OPENAI_API_KEY,
            openai_api_base=self.app_context.env_vars.OPENAI_BASE_URL,
			model=llm_configuration.name,
            temperature=llm_configuration.temperature
        )