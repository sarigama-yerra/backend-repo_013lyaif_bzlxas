"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Example schemas (remain as references)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Peer Assistant Schemas
class Conversation(BaseModel):
    """
    Conversations collection schema
    Collection name: "conversation"
    """
    session_id: str = Field(..., description="Unique session identifier for the chat")
    title: str = Field(..., description="Conversation title")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Message(BaseModel):
    """
    Messages collection schema
    Collection name: "message"
    """
    session_id: str = Field(..., description="Associated session identifier")
    role: str = Field(..., pattern="^(user|assistant|system)$", description="Message role")
    text: str = Field(..., description="Message content")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Existing session id; omit to start new")
    user_text: str = Field(..., min_length=1, description="User message text")

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    messages: Optional[List[Message]] = None
