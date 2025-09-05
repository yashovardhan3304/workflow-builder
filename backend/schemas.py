from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Workflow Schemas
class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class WorkflowCreate(WorkflowBase):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class WorkflowUpdate(WorkflowBase):
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None

class WorkflowResponse(WorkflowBase):
    id: int
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Document Schemas
class DocumentBase(BaseModel):
    filename: str
    file_size: int
    file_type: str

class DocumentCreate(DocumentBase):
    file_path: str

class DocumentResponse(DocumentBase):
    id: int
    content: Optional[str] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Workflow Execution Schemas
class WorkflowExecutionBase(BaseModel):
    query: str

class WorkflowExecutionCreate(WorkflowExecutionBase):
    workflow_id: int

class WorkflowExecutionResponse(WorkflowExecutionBase):
    id: int
    workflow_id: int
    response: Optional[str] = None
    execution_log: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Chat Schemas
class ChatMessageBase(BaseModel):
    query: str
    session_id: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageResponse(ChatMessageBase):
    id: int
    response: Optional[str] = None
    workflow_execution_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Component Configuration Schemas
class UserQueryConfig(BaseModel):
    placeholder: str = "Enter your question here..."
    max_length: int = 1000

class KnowledgeBaseConfig(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "gemini"  # Only Gemini supported
    collection_name: Optional[str] = None

class LLMEngineConfig(BaseModel):
    model: str = "gemini-pro"  # Only Gemini supported
    temperature: float = 0.7
    max_tokens: int = 1000
    use_web_search: bool = False
    custom_prompt: Optional[str] = None

class OutputConfig(BaseModel):
    show_timestamps: bool = True
    enable_follow_up: bool = True
    max_history: int = 50

# Workflow Execution Request
class WorkflowExecutionRequest(BaseModel):
    query: str
    workflow_id: int
    session_id: Optional[str] = None
