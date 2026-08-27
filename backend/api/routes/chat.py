"""
React-Ready AI Agent Chat Route
Provides frontend-independent API endpoint for natural language database querying,
reusing the existing LangGraph ReAct agent, AST validator, and read-only execution.
"""

import uuid
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from backend.config import Settings, get_settings
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.dataset_service import DatasetService
from backend.limiter import limiter
from agents import ask_agent
import database

logger = logging.getLogger("zerosql")

router = APIRouter(prefix="/chat", tags=["AI Agent Chat"])


def infer_visualization_hint(rows: List[Dict[str, Any]]) -> Optional[str]:
    """
    Infers the most appropriate chart visualization type based on result structure.
    """
    if not rows or len(rows) == 0:
        return None

    first_row = rows[0]
    keys = list(first_row.keys())
    if len(keys) < 2:
        return "table"

    numeric_cols = []
    text_cols = []
    date_cols = []

    for k, v in first_row.items():
        if isinstance(v, (int, float)):
            numeric_cols.append(k)
        elif isinstance(v, str):
            if any(term in k.lower() for term in ["date", "time", "month", "year", "day"]):
                date_cols.append(k)
            else:
                text_cols.append(k)

    if date_cols and numeric_cols:
        return "line"
    elif text_cols and numeric_cols:
        if len(rows) <= 5:
            return "pie"
        return "bar"
    elif numeric_cols:
        return "bar"

    return "table"


@router.post(
    "",
    response_model=ChatResponse,
    summary="Query Database in Natural Language",
    description="Sends a natural language question to the AI SQL Agent, executes read-only SQL, and returns structured results."
)
@limiter.limit("10/minute")
def chat_with_agent(
    request: Request,
    payload: ChatRequest,
    settings: Settings = Depends(get_settings)
) -> ChatResponse:
    """
    Frontend-independent Chat API endpoint for React / external clients.
    Reuses existing LangGraph agent, MemorySaver, AST validator, and read-only DB connection.
    """
    clean_message = payload.message.strip()
    if not clean_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty."
        )

    # Resolve thread ID for conversation isolation
    thread_id = payload.thread_id or f"thread_{uuid.uuid4().hex[:8]}"

    # Resolve Active Table Context
    active_table: Optional[str] = None
    dataset_svc = DatasetService(settings)

    if payload.dataset_id:
        ds = dataset_svc.get_dataset_by_id(payload.dataset_id)
        if not ds:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with ID '{payload.dataset_id}' not found."
            )
        if ds.processing_status != "READY" or not ds.table_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset '{ds.dataset_name}' is not in READY status."
            )
        active_table = ds.table_name

    elif payload.table_name:
        # Validate table exists in PostgreSQL
        all_tables = database.get_tables_list()
        if payload.table_name not in all_tables:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table '{payload.table_name}' does not exist in the database."
            )
        active_table = payload.table_name

    # Query through the existing LangGraph ReAct agent pipeline
    try:
        model_name = payload.model_name or settings.groq_model
        agent_resp = ask_agent(
            user_question=clean_message,
            thread_id=thread_id,
            model_name=model_name,
            active_table=active_table
        )
    except Exception as e:
        logger.error(f"AI Agent query execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI Agent query execution failed due to an internal server error."
        )

    answer = agent_resp.get("answer", "")
    sql_query = agent_resp.get("sql_query")
    val_passed = agent_resp.get("validation_passed", True)
    q_res = agent_resp.get("query_result") or {}

    rows = q_res.get("rows", [])
    row_count = q_res.get("row_count", len(rows))
    exec_time = q_res.get("execution_time_ms", 0.0)
    columns = list(rows[0].keys()) if rows else []

    vis_type = infer_visualization_hint(rows) if val_passed and rows else None

    return ChatResponse(
        success=val_passed,
        answer=answer,
        sql_query=sql_query,
        validation_passed=val_passed,
        columns=columns,
        rows=rows,
        row_count=row_count,
        execution_time_ms=exec_time,
        thread_id=thread_id,
        dataset_id=payload.dataset_id,
        table_name=active_table,
        visualization_type=vis_type
    )
