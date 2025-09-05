from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    nodes = Column(JSON, nullable=False)  # React Flow nodes
    edges = Column(JSON, nullable=False)  # React Flow edges
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    executions = relationship("WorkflowExecution", back_populates="workflow")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=True)  # Extracted text
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    embeddings = relationship("DocumentEmbedding", back_populates="document")

class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding_vector = Column(JSON, nullable=False)  # Store as JSON array
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="embeddings")

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    execution_log = Column(JSON, nullable=True)  # Store execution steps
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    workflow_execution_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    workflow_execution = relationship("WorkflowExecution")
