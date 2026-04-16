from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
import uvicorn

from src.Rag_concept.rag_based_chatbot import main

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Indian College Explorer API",
    description="AI-powered chatbot with detailed info on 45+ curated Indian colleges",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class QuestionRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    question: str
    answer: str


# Initialize chatbot
chatbot = main()


# --------------------------------------------------
# Endpoints
# --------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(request: QuestionRequest):
    """Main chatbot endpoint — ask any question about Indian colleges."""
    answer = chatbot(request.question)
    return ChatResponse(question=request.question, answer=answer)


@app.get("/search")
def search_colleges(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, description="Max results")
):
    """Search colleges by name."""
    results = chatbot.search(q, limit)
    return {"query": q, "count": len(results), "colleges": results}


@app.get("/colleges")
def get_all_colleges():
    """Get all colleges with basic info."""
    colleges = chatbot.get_all_colleges_api()
    return {"count": len(colleges), "colleges": colleges}


@app.get("/college/{college_id}")
def get_college_detail(college_id: int):
    """Get full details of a specific college."""
    college = chatbot.get_college_detail_api(college_id)
    if college:
        return college
    return {"error": "College not found"}


@app.get("/stats")
def get_stats():
    """Get database statistics."""
    return chatbot.get_stats()


@app.get("/states")
def get_states():
    """Get all available states."""
    states = chatbot.get_states()
    return {"count": len(states), "states": states}


@app.get("/colleges/by-state")
def colleges_by_state(
    state: str = Query(..., description="State name"),
    limit: int = Query(50, description="Max results")
):
    """Get colleges filtered by state."""
    colleges = chatbot.get_colleges_by_state(state, limit)
    return {"state": state, "count": len(colleges), "colleges": colleges}


@app.get("/colleges/by-district")
def colleges_by_district(
    district: str = Query(..., description="District name"),
    limit: int = Query(50, description="Max results")
):
    """Get colleges filtered by district."""
    colleges = chatbot.get_colleges_by_district(district, limit)
    return {"district": district, "count": len(colleges), "colleges": colleges}
