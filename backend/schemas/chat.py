"""
React-Ready Chat & Natural Language Query Schemas
Defines request and response payload structures for frontend-independent AI SQL Agent interaction.
"""

import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Payload sent by React / external frontends to query the AI SQL Agent."""
    message: str = Field(..., min_length=1, max_length=2000, description="Natural language user question")
    thread_id: Optional[str] = Field(default=None, description="Conversation thread identifier for multi-turn memory")
    dataset_id: Optional[str] = Field(default=None, description="Optional UUID of active dataset context")
    table_name: Optional[str] = Field(default=None, description="Optional direct PostgreSQL table name")
    model_name: Optional[str] = Field(default=None, description="Optional Groq model override")


class ChatResponse(BaseModel):
    """Structured, frontend-ready response from the AI SQL Agent."""
    success: bool = Field(default=True, description="Query execution status")
    answer: str = Field(description="Natural language markdown explanation from AI Agent")
    sql_query: Optional[str] = Field(default=None, description="AST-validated SQL query executed by the agent")
    validation_passed: bool = Field(default=True, description="Whether SQL passed AST security validator")
    columns: List[str] = Field(default_factory=list, description="Column names returned in dataset result")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="Row records formatted as JSON objects")
    row_count: int = Field(default=0, description="Number of rows returned")
    execution_time_ms: float = Field(default=0.0, description="Database execution latency in milliseconds")
    thread_id: str = Field(description="Conversation thread ID preserved across turns")
    dataset_id: Optional[str] = Field(default=None, description="Active dataset UUID")
    table_name: Optional[str] = Field(default=None, description="Active PostgreSQL table name")
    visualization_type: Optional[str] = Field(default=None, description="Suggested chart type: 'bar', 'line', 'pie', 'table'")
