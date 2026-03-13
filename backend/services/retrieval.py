"""
RAG retrieval helpers – entity inference, similarity search, query building.
"""

from typing import Optional

from config import RETRIEVAL_TOP_K
from vector_database import vector_store


def _infer_entity_type(query: str) -> Optional[str]:
    lowered = query.lower()
    if any(keyword in lowered for keyword in ["doctor", "doctors", "dr.", "physician", "specialist"]):
        return "doctor"
    if any(keyword in lowered for keyword in ["department", "departments", "cardiology", "orthopedic", "neurology"]):
        return "department"
    if any(keyword in lowered for keyword in ["hospital", "hospitals", "clinic", "medical center"]):
        return "hospital"
    return None


def retrieve_relevant_chunks(query: str):
    entity_type = _infer_entity_type(query)

    if entity_type:
        filtered_chunks = vector_store.similarity_search(
            query,
            k=RETRIEVAL_TOP_K,
            filter={"entity_type": entity_type},
        )
        if filtered_chunks:
            return filtered_chunks

    return vector_store.similarity_search(query, k=RETRIEVAL_TOP_K)


def has_local_data(chunks) -> bool:
    return any(getattr(chunk, "page_content", "").strip() for chunk in chunks)


def build_grounded_user_query(message: str, content: str) -> str:
    if content:
        return (
            f"Question: {message}\n"
            f"relevant context: {content}\n"
            "Instructions: Answer only from the relevant context above. "
            "If the answer is not present, clearly say that the requested information is not available in the current data.\n"
            "Answer:"
        )

    return (
        f"Question: {message}\n"
        "Instructions: No relevant local context was retrieved. "
        "If this is about hospitals, departments, or doctors in local data, say it is not available. "
        "Use websearch only for real-time or general web information.\n"
        "Answer:"
    )
