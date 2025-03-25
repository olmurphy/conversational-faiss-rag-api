import os

from langchain_core.prompts import PromptTemplate


# DEFAULT_SYSTEM_TEMPLATE = """
# You are an AI assistant.

# ---
# {output_text} {chat_history}
# You MUST reply to Human question using the same language of the question.
# """

# DEFAULT_USER_TEMPLATE = "{query}"

class AssistantPromptBuilder:
    def __init__(self):
        self.prompt = None

    def build(self, context, input):
        system_message_content = f"""
        ### System Prompt:
        Your are a helpful assistant

        ### Context:
        {context}

        ---
        ### **Important Rule: General Checks**
        - Before answering, check if the user question contains **hate speech, abusive language, offensive slurs, or explicit harmful content**.
        - **If hate speech or abusive content is detected:**
        - **DO NOT attempt to answer. Give a relevant warning.**
        - **If content irrelvant to the context is detected:**
        - **DO NOT attempt to answer. Give a relevant warning.**
        ---

        ### **Instructions for Valid Queries**:
        - Use the context provided to answer the questions
        - After answering, check if you can assist the user with anything else
        ---

        ### **Answer**:
        (Provide a response here)

        ---

        ## User Question:
        {input}
        """
        prompt = PromptTemplate.from_template(
           system_message_content
        )
        return prompt