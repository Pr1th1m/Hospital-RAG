"""
Web search via Tavily – thin wrapper used by chat services.
"""

from config import tavily_client


def websearch(query: str) -> str:
    print("Tool calling...")
    if tavily_client is None:
        return "Web search is currently unavailable."

    responses = tavily_client.search(query)
    return "\n\n".join(response["content"] for response in responses.get("results", []))
