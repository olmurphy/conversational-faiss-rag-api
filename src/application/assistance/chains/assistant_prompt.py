import os

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


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

    def build(self, context):
        system_message_content = f"""


### Instructions:
You are an expert in merchandising, inventory management, and retail analytics. Your task is to provide accurate and concise answers to user questions.
### Context:
{context}

### **Instructions**:
- Use the document content and metadata to generate an answer. The document contains either a report or an application. 
- You have to answer the question by giving the user the name of the application or the report and anything else mentioned in the context. 
- Use the metadata to answer 
- Suggest Follow-Up Questions*: Based on the context and conversation, suggest 2-3 logical follow-up questions that the user might ask next. **These questions MUST be directly tied to the data in the provided context. Avoid generic or unrelated questions. 

### **Example Question and Expected Answer:**

- **User Question**: *How can I create product variant groups?*  
- **Expected LLM Answer**:  
  *You can use the Merch Hub application - 'Product Variants' to perform this.*

### **Answer**:
(Provide a response here)

## **Follow-Up Questions**:
(Provide follow up questions here)

"""

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_message_content),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        return prompt