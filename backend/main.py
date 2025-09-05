from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
import fitz
import chromadb
import openai
from openai import OpenAI

from database import get_db, engine
from models import Base
from schemas import (
    WorkflowCreate, WorkflowResponse, WorkflowUpdate,
    DocumentResponse, WorkflowExecutionResponse,
    ChatMessageResponse, WorkflowExecutionRequest
)
from workflow_engine import WorkflowEngine
from components.factory import ComponentFactory
from config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="No-Code Workflow Application",
    description="A visual workflow builder for intelligent document processing and LLM interactions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize workflow engine
workflow_engine = WorkflowEngine()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "No-Code Workflow Application API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

# Component Management Endpoints
@app.get("/api/components")
async def get_available_components():
    """Get list of available workflow components"""
    try:
        components = ComponentFactory.get_available_components()
        component_schemas = {}
        
        for component_type in components:
            try:
                schema = ComponentFactory.get_component_schema(component_type)
                component_schemas[component_type] = schema
            except Exception as e:
                component_schemas[component_type] = {"error": str(e)}
        
        return {
            "components": components,
            "schemas": component_schemas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting components: {str(e)}")

@app.get("/api/components/{component_type}/schema")
async def get_component_schema(component_type: str):
    """Get schema for a specific component type"""
    try:
        schema = ComponentFactory.get_component_schema(component_type)
        return schema
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting schema: {str(e)}")

# Workflow Management Endpoints
@app.post("/api/workflows", response_model=WorkflowResponse)
async def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    """Create a new workflow"""
    try:
        # Create workflow in database
        from models import Workflow
        db_workflow = Workflow(
            name=workflow.name,
            description=workflow.description,
            nodes=workflow.nodes,
            edges=workflow.edges
        )
        
        db.add(db_workflow)
        db.commit()
        db.refresh(db_workflow)
        
        return db_workflow
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating workflow: {str(e)}")

@app.get("/api/workflows", response_model=List[WorkflowResponse])
async def list_workflows(db: Session = Depends(get_db)):
    """List all workflows"""
    try:
        from models import Workflow
        workflows = db.query(Workflow).filter(Workflow.is_active == True).all()
        return workflows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing workflows: {str(e)}")

@app.get("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Get a specific workflow"""
    try:
        from models import Workflow
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return workflow
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow: {str(e)}")

@app.put("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int, 
    workflow_update: WorkflowUpdate, 
    db: Session = Depends(get_db)
):
    """Update a workflow"""
    try:
        from models import Workflow
        db_workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not db_workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update fields
        if workflow_update.name is not None:
            db_workflow.name = workflow_update.name
        if workflow_update.description is not None:
            db_workflow.description = workflow_update.description
        if workflow_update.nodes is not None:
            db_workflow.nodes = workflow_update.nodes
        if workflow_update.edges is not None:
            db_workflow.edges = workflow_update.edges
        if workflow_update.is_active is not None:
            db_workflow.is_active = workflow_update.is_active
        
        db.commit()
        db.refresh(db_workflow)
        
        return db_workflow
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating workflow: {str(e)}")

@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Delete a workflow (soft delete)"""
    try:
        from models import Workflow
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow.is_active = False
        db.commit()
        
        return {"message": "Workflow deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting workflow: {str(e)}")

# Workflow Execution Endpoints
@app.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: int,
    execution_request: WorkflowExecutionRequest,
    db: Session = Depends(get_db)
):
    """Execute a workflow with a query"""
    try:
        # Get workflow
        from models import Workflow
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if not workflow.is_active:
            raise HTTPException(status_code=400, detail="Workflow is not active")
        
        # Validate before execution with detailed reason
        is_valid, reason = workflow_engine._validate_workflow_with_reason(
            workflow.nodes or [], workflow.edges or []
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid workflow: {reason}")

        # Execute workflow
        execution_result = await workflow_engine.execute_workflow(
            {
                "id": workflow_id,
                "nodes": workflow.nodes,
                "edges": workflow.edges
            },
            execution_request.query
        )
        
        if not execution_result["success"]:
            raise HTTPException(status_code=500, detail=execution_result["error"])
        
        # Determine Output node id and extract formatted response
        output_node_id = None
        try:
            for n in (workflow.nodes or []):
                if (n.get("data") or {}).get("type") == "output":
                    output_node_id = n.get("id")
                    break
        except Exception:
            output_node_id = None
        output_payload = {}
        if output_node_id:
            output_payload = (execution_result.get("results") or {}).get(output_node_id, {})
        formatted_response = output_payload.get("formatted_response", "")

        # Store execution record
        from models import WorkflowExecution
        execution_record = WorkflowExecution(
            workflow_id=workflow_id,
            query=execution_request.query,
            response=formatted_response,
            execution_log=execution_result["execution_log"],
            status="completed"
        )
        
        db.add(execution_record)
        db.commit()
        db.refresh(execution_record)
        
        return {
            "success": True,
            "execution_id": execution_record.id,
            "results": execution_result["results"],
            "execution_log": execution_result["execution_log"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error executing workflow: {str(e)}")

# Document Management Endpoints
@app.post("/api/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection_name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload and process a document"""
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Create upload directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{file.filename}")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text from PDF using PyMuPDF
        content_text = ""
        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    content_text += page.get_text("text") + "\n"
        except Exception as e:
            content_text = ""
        
        # Store in database
        from models import Document
        # Persist basic metadata; include collection name in extra_metadata for filtering
        document = Document(
            filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            file_type="pdf",
            content=content_text,
            extra_metadata={"collection_name": (collection_name or "default")}
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Index into ChromaDB (basic, synchronous)
        try:
            # Disable Chroma telemetry noise
            try:
                os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"
            except Exception:
                pass
            chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
            collection = None
            try:
                target_collection = (collection_name or settings.chroma_persist_directory and "default") or "default"
                collection = chroma_client.get_collection(target_collection)
            except Exception:
                target_collection = (collection_name or "default")
                collection = chroma_client.create_collection(name=target_collection, metadata={"description": f"Collection {target_collection}"})

            # Simple chunking
            def chunk_text(text: str, size: int = 800, overlap: int = 200):
                chunks = []
                start = 0
                length = len(text)
                while start < length:
                    end = min(start + size, length)
                    chunk = text[start:end]
                    chunks.append(chunk)
                    if end == length:
                        break
                    start = end - overlap
                    if start < 0:
                        start = 0
                return chunks

            chunks = chunk_text(content_text or "")

            # Embeddings
            def embed_batch(texts: list[str]) -> list[list[float]]:
                if not texts:
                    return []
                if settings.openai_api_key:
                    try:
                        client = OpenAI(api_key=settings.openai_api_key)
                        resp = client.embeddings.create(input=texts, model="text-embedding-3-small")
                        return [d.embedding for d in resp.data]
                    except Exception:
                        pass
                # Fallback mock vectors
                return [[0.0] * 1536 for _ in texts]

            embeddings = embed_batch(chunks)
            ids = [f"doc_{document.id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [{"document_id": document.id, "filename": document.filename, "source": document.file_path, "chunk_index": i, "collection_name": (collection_name or "default")} for i in range(len(chunks))]

            if chunks:
                try:
                    collection.add(documents=chunks, embeddings=embeddings, metadatas=metadatas, ids=ids)
                except Exception:
                    # If add fails (e.g., dimension mismatch), proceed without blocking upload
                    pass
        except Exception:
            # Silently ignore indexing failures for now
            pass

        return document
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@app.get("/api/documents", response_model=List[DocumentResponse])
async def list_documents(collection: Optional[str] = None, db: Session = Depends(get_db)):
    """List all documents"""
    try:
        from models import Document
        q = db.query(Document)
        if collection:
            q = q.filter((Document.extra_metadata["collection_name"].as_string() == collection))
        documents = q.all()
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.get("/api/collections")
async def list_collections():
    """List available Chroma collections"""
    try:
        os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"
        chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
        # Chroma doesn't have a direct list API in some versions; try common pattern
        collections = []
        try:
            collections = [c.name for c in chroma_client.list_collections()]
        except Exception:
            # Fallback: ensure default exists
            try:
                chroma_client.get_collection("default")
            except Exception:
                chroma_client.create_collection(name="default", metadata={"description": "Default document collection"})
            collections = ["default"]
        return {"collections": collections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing collections: {str(e)}")

# Chat Endpoints
@app.post("/api/chat")
async def chat_with_workflow(
    chat_request: WorkflowExecutionRequest,
    db: Session = Depends(get_db)
):
    """Chat interface that executes workflows"""
    try:
        # Execute workflow
        execution_result = await execute_workflow(
            chat_request.workflow_id,
            chat_request,
            db
        )
        
        if not execution_result["success"]:
            raise HTTPException(status_code=500, detail="Workflow execution failed")
        
        # Get the final response from Output node
        # We need to look it up from DB to access nodes
        from models import Workflow
        wf = db.query(Workflow).filter(Workflow.id == chat_request.workflow_id).first()
        output_node_id = None
        try:
            for n in (wf.nodes or []):
                if (n.get("data") or {}).get("type") == "output":
                    output_node_id = n.get("id")
                    break
        except Exception:
            output_node_id = None
        output_payload = {}
        if output_node_id:
            output_payload = (execution_result.get("results") or {}).get(output_node_id, {})
        response_text = output_payload.get("formatted_response", "No response generated")
        
        return {
            "success": True,
            "response": response_text,
            "execution_id": execution_result["execution_id"],
            "follow_up_suggestions": output_payload.get("follow_up_suggestions", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")

# Execution Logs
@app.get("/api/executions/logs")
async def get_execution_logs(limit: int = 100):
    """Get recent workflow execution logs"""
    try:
        logs = workflow_engine.get_execution_log(limit)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")

@app.patch("/api/workflows/{workflow_id}/update-model")
async def update_workflow_model(workflow_id: int, model: str, db: Session = Depends(get_db)):
    """Update the model in all LLM nodes of a workflow"""
    try:
        from models import Workflow
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update all LLM nodes to use the new model
        updated_nodes = []
        for node in workflow.nodes:
            if node.get("data", {}).get("type") == "llm_engine":
                # Update the model in the node's config
                if "config" not in node["data"]:
                    node["data"]["config"] = {}
                node["data"]["config"]["model"] = model
            updated_nodes.append(node)
        
        workflow.nodes = updated_nodes
        db.commit()
        db.refresh(workflow)
        
        return {"message": f"Updated all LLM nodes to use model: {model}"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating workflow model: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
