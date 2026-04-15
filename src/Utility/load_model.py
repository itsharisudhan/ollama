from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from config import Settings
from functools import lru_cache
import os
from dotenv import load_dotenv
load_dotenv()


@lru_cache
def load_embeddings():
    embeddings = HuggingFaceEmbeddings(
        model=Settings().EMBEDDING_MODEL
    )
    
    return embeddings



def load_llm_model():
    llm = ChatGroq(
        model=Settings().LLM_MODEL,
        api_key=Settings().GROQ_API_KEY,
        temperature=Settings().TEMPERATURE
    )

    return llm


# def load_llm_model():
#     llm = ChatOllama(
#         base_url="http://localhost:11434",
#         model=Settings().OLLAMA_MODEL,
#         temperature=Settings().TEMPERATURE
#     )

#     return llm