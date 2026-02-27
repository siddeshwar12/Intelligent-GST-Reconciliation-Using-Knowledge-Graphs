"""Chatbot API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict
import sys
from pathlib import Path

# Add chatbot to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from chatbot.knowledge_base import get_answer

router = APIRouter(tags=["chatbot"])

class ChatMessage(BaseModel):
    """Chat message model."""
    message: str

class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    timestamp: str

# Store chat history (in production, use database)
chat_history: List[Dict[str, str]] = []

@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Process chat message and return response.
    
    Args:
        message: User's chat message
        
    Returns:
        Bot's response
    """
    from datetime import datetime
    
    # Get response from knowledge base
    response = get_answer(message.message)
    
    # Store in history
    timestamp = datetime.now().isoformat()
    chat_history.append({
        "user": message.message,
        "bot": response,
        "timestamp": timestamp
    })
    
    # Keep only last 50 messages
    if len(chat_history) > 50:
        chat_history.pop(0)
    
    return ChatResponse(
        response=response,
        timestamp=timestamp
    )

@router.get("/chat/history")
async def get_chat_history():
    """Get chat history."""
    return {"history": chat_history}

@router.delete("/chat/history")
async def clear_chat_history():
    """Clear chat history."""
    chat_history.clear()
    return {"message": "Chat history cleared"}
