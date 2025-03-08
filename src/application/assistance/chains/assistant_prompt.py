from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class AssistantPromptBuilder:
    def __init__(self):
        self.prompt = None

    def build(self, context):
        system_message_content = f"""

### Instructions:
Your a a helpful bot
### Context:
{context}
### **Instructions**:
- answer the question
### **Answer**:
Answer goes here
"""

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_message_content),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        return prompt
