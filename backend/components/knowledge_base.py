import chromadb
from typing import Dict, Any, List
from .base import BaseComponent, ComponentConfig, ComponentResult
from config import settings
import google.generativeai as genai
import asyncio
import re

class KnowledgeBaseComponent(BaseComponent):
    """Component for document processing and vector search"""
    
    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        self.chunk_size = config.config.get("chunk_size", 1000)
        self.chunk_overlap = config.config.get("chunk_overlap", 200)
        self.embedding_model = "gemini"  # Only Gemini supported
        raw_collection_name = config.config.get("collection_name", "default")
        self.collection_name = self._sanitize_collection_name(raw_collection_name)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory
        )
        
        # Initialize Gemini for embeddings
        if settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)
    
    def _sanitize_collection_name(self, name: str) -> str:
        """Sanitize collection name to meet ChromaDB requirements"""
        if not name:
            return "default"
        
        # Remove file extension if present
        name = name.split('.')[0]
        
        # Replace invalid characters with underscores
        # Keep only alphanumeric, underscores, and hyphens
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Ensure it starts and ends with alphanumeric
        sanitized = re.sub(r'^[^a-zA-Z0-9]+', '', sanitized)
        sanitized = re.sub(r'[^a-zA-Z0-9]+$', '', sanitized)
        
        # Ensure length is between 3-63 characters
        if len(sanitized) < 3:
            sanitized = f"collection_{sanitized}" if sanitized else "default"
        elif len(sanitized) > 63:
            sanitized = sanitized[:63]
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = "default"
            
        return sanitized
    
    async def execute(self, inputs: Dict[str, Any]) -> ComponentResult:
        """Execute the knowledge base component"""
        try:
            query = inputs.get("query", "")
            if not query:
                return ComponentResult(
                    success=False,
                    error="No query provided for knowledge base search"
                )
            
            # Get or create collection
            collection = self._get_or_create_collection()
            
            # Search for relevant documents
            results = await self._search_documents(collection, query)
            
            if not results:
                return ComponentResult(
                    success=True,
                    data={
                        "context": "",
                        "documents_found": 0,
                        "query": query
                    },
                    metadata={
                        "component_type": "knowledge_base",
                        "component_id": self.component_id,
                        "embedding_model": self.embedding_model
                    }
                )
            
            # Combine relevant context
            context = self._combine_context(results)
            
            return ComponentResult(
                success=True,
                data={
                    "context": context,
                    "documents_found": len(results),
                    "query": query,
                    "sources": [r.get("metadata", {}).get("source", "") for r in results]
                },
                metadata={
                    "component_type": "knowledge_base",
                    "component_id": self.component_id,
                    "embedding_model": self.embedding_model,
                    "collection_name": self.collection_name
                }
            )
            
        except Exception as e:
            return ComponentResult(
                success=False,
                error=f"Error in knowledge base component: {str(e)}"
            )
    
    def _get_or_create_collection(self):
        """Get or create ChromaDB collection"""
        try:
            collection = self.chroma_client.get_collection(self.collection_name)
        except:
            collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": f"Collection for {self.collection_name}"}
            )
        return collection
    
    async def _search_documents(self, collection, query: str, n_results: int = 5):
        """Search for relevant documents"""
        try:
            # Generate query embedding (with safe fallback if no keys configured)
            query_embedding = await self._generate_embedding(query)
            
            # Search in ChromaDB
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results["documents"]:
                for i in range(len(results["documents"][0])):
                    formatted_results.append({
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Gemini"""
        if not settings.google_api_key:
            return [0.0] * 1536

        try:
            # Gemini embeddings API (v1) via Embeddings.create
            genai.configure(api_key=settings.google_api_key)
            # Prefer 1.5 embedding model; fall back to embedding-001
            models = [
                "models/embedding-001",
                "text-embedding-004"
            ]
            last_error = None
            for m in models:
                try:
                    resp = genai.embed_content(model=m, content=text)
                    vec = resp.get("embedding") or resp.get("data", [{}])[0].get("embedding")
                    if vec:
                        return vec
                except Exception as ie:
                    last_error = ie
                    continue
            raise last_error if last_error else Exception("Unknown embedding error")
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * 1536
    
    def _combine_context(self, results: List[Dict]) -> str:
        """Combine search results into context"""
        context_parts = []
        for result in results:
            doc = result.get("document", "")
            if doc:
                context_parts.append(doc)
        
        return "\n\n".join(context_parts)
    
    def validate_config(self) -> bool:
        """Validate component configuration"""
        return (
            isinstance(self.chunk_size, int) and
            isinstance(self.chunk_overlap, int) and
            self.chunk_size > 0 and
            self.chunk_overlap >= 0 and
            self.chunk_overlap < self.chunk_size and
            self.embedding_model == "gemini"
        )
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the expected input schema"""
        return {
            "query": {
                "type": "string",
                "description": "Query to search in knowledge base",
                "required": True
            }
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema"""
        return {
            "context": {
                "type": "string",
                "description": "Relevant context from documents"
            },
            "documents_found": {
                "type": "integer",
                "description": "Number of relevant documents found"
            },
            "query": {
                "type": "string",
                "description": "Original search query"
            },
            "sources": {
                "type": "array",
                "description": "List of document sources"
            }
        }
    
    def get_required_inputs(self) -> list[str]:
        """Get required input keys"""
        return ["query"]
    
    def get_optional_inputs(self) -> list[str]:
        """Get optional input keys"""
        return []
