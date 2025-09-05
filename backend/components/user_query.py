from typing import Dict, Any
from .base import BaseComponent, ComponentConfig, ComponentResult

class UserQueryComponent(BaseComponent):
    """Component for handling user queries"""
    
    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        self.placeholder = config.config.get("placeholder", "Enter your question here...")
        self.max_length = config.config.get("max_length", 1000)
    
    async def execute(self, inputs: Dict[str, Any]) -> ComponentResult:
        """Execute the user query component"""
        try:
            query = inputs.get("query", "")
            
            if not query:
                return ComponentResult(
                    success=False,
                    error="No query provided"
                )
            
            if len(query) > self.max_length:
                return ComponentResult(
                    success=False,
                    error=f"Query exceeds maximum length of {self.max_length} characters"
                )
            
            return ComponentResult(
                success=True,
                data={
                    "query": query,
                    "query_length": len(query),
                    "timestamp": inputs.get("timestamp")
                },
                metadata={
                    "component_type": "user_query",
                    "component_id": self.component_id
                }
            )
            
        except Exception as e:
            return ComponentResult(
                success=False,
                error=f"Error processing user query: {str(e)}"
            )
    
    def validate_config(self) -> bool:
        """Validate component configuration"""
        return (
            isinstance(self.placeholder, str) and
            isinstance(self.max_length, int) and
            self.max_length > 0
        )
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the expected input schema"""
        return {
            "query": {
                "type": "string",
                "description": "User's question or query",
                "required": True
            },
            "timestamp": {
                "type": "string",
                "description": "Timestamp of the query",
                "required": False
            }
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema"""
        return {
            "query": {
                "type": "string",
                "description": "Processed user query"
            },
            "query_length": {
                "type": "integer",
                "description": "Length of the query"
            },
            "timestamp": {
                "type": "string",
                "description": "Query timestamp"
            }
        }
    
    def get_required_inputs(self) -> list[str]:
        """Get required input keys"""
        return ["query"]
    
    def get_optional_inputs(self) -> list[str]:
        """Get optional input keys"""
        return ["timestamp"]
