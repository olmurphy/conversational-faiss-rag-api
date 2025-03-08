import redis
import json
from langchain.schema import HumanMessage, AIMessage

def serialize_message(message):
    """Serializes a HumanMessage or AIMessage to a JSON string."""
    if isinstance(message, HumanMessage):
        return json.dumps({
            "type": "human",
            "content": message.content,
            "additional_kwargs": message.additional_kwargs,
            "response_metadata": message.response_metadata,
        })
    elif isinstance(message, AIMessage):
        return json.dumps({
            "type": "ai",
            "content": message.content,
            "additional_kwargs": message.additional_kwargs,
            "response_metadata": message.response_metadata,
        })
    else:
        raise ValueError("Unsupported message type")

def deserialize_message(message_str):
    """Deserializes a JSON string back to a HumanMessage or AIMessage."""
    message_dict = json.loads(message_str)
    if message_dict["type"] == "human":
        return HumanMessage(
            content=message_dict["content"],
            additional_kwargs=message_dict["additional_kwargs"],
            response_metadata=message_dict["response_metadata"],
        )
    elif message_dict["type"] == "ai":
        return AIMessage(
            content=message_dict["content"],
            additional_kwargs=message_dict["additional_kwargs"],
            response_metadata=message_dict["response_metadata"],
        )
    else:
        raise ValueError("Unknown message type")