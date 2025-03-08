from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from context import AppContext

class EmbeddingsManager:
    def __init__(self, app_context: AppContext):
        self.app_context = app_context

    def get_embeddings_instance(self) -> Embeddings:
        embeddings_configuration = self.app_context.configurations.embeddings
        encode_kwargs = {'normalize_embeddings': embeddings_configuration.normalize_embeddings}
        return HuggingFaceEmbeddings(model_name=embeddings_configuration.name, encode_kwargs=encode_kwargs)