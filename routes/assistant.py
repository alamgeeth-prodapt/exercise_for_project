"""
FastAPI router for the Telecom Churn AI Assistant.
Integrates with Anthropic Claude API, manages persistent conversation history,
and executes agentic tool calls on backend routes and ML models.
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import anthropic

from database import get_db, AssistantConversation, AssistantMessage
from routes.auth import get_current_user
from routes.assistant_prompt import CHURN_ASSISTANT_SYSTEM_PROMPT
from routes.assistant_tools import ANTHROPIC_TOOLS, execute_tool

load_dotenv()

router = APIRouter(
    prefix="/assistant",
    tags=["Churn Assistant"],
    dependencies=[Depends(get_current_user)]
)

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")


# ==============================================================================
# SCHEMAS
# ==============================================================================

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class MessageItem(BaseModel):
    message_id: int
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    created_at: datetime


class ConversationSummary(BaseModel):
    conversation_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ChatResponse(BaseModel):
    conversation_id: str
    title: str
    reply: str
    tool_calls: List[Dict[str, Any]]
    created_at: datetime


# ==============================================================================
# ENDPOINTS
# ==============================================================================

@router.get("/conversations", response_model=List[ConversationSummary])
def list_conversations(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all chat conversations for the currently logged-in user, ordered by most recently updated.
    """
    convs = (
        db.query(AssistantConversation)
        .filter(AssistantConversation.username == current_user)
        .order_by(AssistantConversation.updated_at.desc())
        .all()
    )

    summaries = []
    for c in convs:
        summaries.append(
            ConversationSummary(
                conversation_id=c.conversation_id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=len(c.messages)
            )
        )
    return summaries


@router.post("/conversations", response_model=ConversationSummary)
def create_conversation(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new empty conversation session.
    """
    new_id = str(uuid.uuid4())
    conv = AssistantConversation(
        conversation_id=new_id,
        username=current_user,
        title="New Conversation"
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    return ConversationSummary(
        conversation_id=conv.conversation_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0
    )


@router.get("/conversations/{conversation_id}", response_model=List[MessageItem])
def get_conversation_history(
    conversation_id: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all message records for a specific conversation.
    """
    conv = (
        db.query(AssistantConversation)
        .filter(
            AssistantConversation.conversation_id == conversation_id,
            AssistantConversation.username == current_user
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    items = []
    for m in conv.messages:
        tools = None
        if m.tool_calls:
            try:
                tools = json.loads(m.tool_calls)
            except Exception:
                tools = None

        items.append(
            MessageItem(
                message_id=m.message_id,
                role=m.role,
                content=m.content,
                tool_calls=tools,
                created_at=m.created_at
            )
        )
    return items


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation thread and all its messages.
    """
    conv = (
        db.query(AssistantConversation)
        .filter(
            AssistantConversation.conversation_id == conversation_id,
            AssistantConversation.username == current_user
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conv)
    db.commit()
    return {"status": "success", "message": "Conversation deleted successfully."}


@router.post("/chat", response_model=ChatResponse)
def chat_with_assistant(
    req: ChatRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Interact with Claude Churn Assistant. Remembers full conversation context,
    invokes backend data/prediction tools dynamically, and persists replies.
    """
    user_prompt = req.message.strip()
    if not user_prompt:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY environment variable is not set. Please add it to your .env file."
        )

    # 1. Retrieve or initialize conversation session
    conv = None
    if req.conversation_id:
        conv = (
            db.query(AssistantConversation)
            .filter(
                AssistantConversation.conversation_id == req.conversation_id,
                AssistantConversation.username == current_user
            )
            .first()
        )

    if not conv:
        # Create a new conversation
        conv_id = req.conversation_id or str(uuid.uuid4())
        # Generate initial title from prompt
        title = user_prompt[:45] + ("…" if len(user_prompt) > 45 else "")
        conv = AssistantConversation(
            conversation_id=conv_id,
            username=current_user,
            title=title
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # If existing conversation still has default title, update it
    if conv.title == "New Conversation":
        conv.title = user_prompt[:45] + ("…" if len(user_prompt) > 45 else "")

    # 2. Build Anthropic messages payload from history
    messages_payload: List[Dict[str, Any]] = []

    for msg in conv.messages:
        messages_payload.append({
            "role": msg.role,
            "content": msg.content
        })

    # Add current user prompt
    messages_payload.append({
        "role": "user",
        "content": user_prompt
    })

    # 3. Agentic loop with Claude and tools
    client = anthropic.Anthropic(api_key=api_key)
    model = os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)

    executed_tools_summary: List[Dict[str, Any]] = []
    max_tool_iterations = 6
    iteration = 0
    final_reply_text = ""

    try:
        while iteration < max_tool_iterations:
            iteration += 1

            response = client.messages.create(
                model=model,
                max_tokens=2500,
                system=CHURN_ASSISTANT_SYSTEM_PROMPT,
                messages=messages_payload,
                tools=ANTHROPIC_TOOLS
            )

            # If Claude wants to execute tools
            if response.stop_reason == "tool_use":
                # Add assistant's response to the conversation history
                messages_payload.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Execute all tool requests and assemble tool results
                tool_results_content = []

                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_id = block.id

                        # Execute the tool
                        result = execute_tool(tool_name, tool_input, db)

                        executed_tools_summary.append({
                            "tool": tool_name,
                            "input": tool_input,
                            "status": "success" if "error" not in result else "error"
                        })

                        tool_results_content.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(result, default=str)
                        })

                # Send tool results back to Claude
                messages_payload.append({
                    "role": "user",
                    "content": tool_results_content
                })

            else:
                # Completed turn: extract text content
                text_parts = []
                for block in response.content:
                    if hasattr(block, "text"):
                        text_parts.append(block.text)

                final_reply_text = "".join(text_parts).strip()
                break

    except anthropic.APIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Anthropic API communication error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while processing assistant chat: {str(e)}"
        )

    if not final_reply_text:
        final_reply_text = "I analyzed the data, but could not formulate a response. Please rephrase or try again."

    # 4. Persist messages to database
    now = datetime.utcnow()

    # Save User message
    user_msg_record = AssistantMessage(
        conversation_id=conv.conversation_id,
        role="user",
        content=user_prompt,
        tool_calls=None,
        created_at=now
    )
    db.add(user_msg_record)

    # Save Assistant message
    tools_json = json.dumps(executed_tools_summary) if executed_tools_summary else None
    assistant_msg_record = AssistantMessage(
        conversation_id=conv.conversation_id,
        role="assistant",
        content=final_reply_text,
        tool_calls=tools_json,
        created_at=now
    )
    db.add(assistant_msg_record)

    conv.updated_at = now
    db.commit()

    return ChatResponse(
        conversation_id=conv.conversation_id,
        title=conv.title,
        reply=final_reply_text,
        tool_calls=executed_tools_summary,
        created_at=now
    )
