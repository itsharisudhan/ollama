from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from config import Settings
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


@lru_cache
def load_embeddings():
    """Load HuggingFace embedding model for vector search."""
    embeddings = HuggingFaceEmbeddings(
        model_name=Settings().EMBEDDING_MODEL
    )
    return embeddings


def load_llm_model():
    """Load Groq LLM for chat responses (cloud-based, no local GPU needed)."""
    llm = ChatGroq(
        model=Settings().LLM_MODEL,
        api_key=Settings().GROQ_API_KEY,
        temperature=Settings().TEMPERATURE
    )
    return llm