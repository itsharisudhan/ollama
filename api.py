from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
# Import your existing RAG backend
from src.Rag_concept.rag_based_chatbot import main

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Admission Chatbot API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request body model
class QuestionRequest(BaseModel):
    question: str

rag = main()

# POST endpoint
@app.post("/chat")
def chat(request: QuestionRequest):

    answer = rag(request.question)
    print("answer is",answer)
    return {
        "question": request.question,
        "answer": answer
    }
