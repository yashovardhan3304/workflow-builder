from typing import Dict, Any
from .base import BaseComponent, ComponentConfig, ComponentResult
from datetime import datetime

class OutputComponent(BaseComponent):
    """Component for handling final output and chat interface"""
    
    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        self.show_timestamps = config.config.get("show_timestamps", True)
        self.enable_follow_up = config.config.get("enable_follow_up", True)
        self.max_history = config.config.get("max_history", 50)
    
    async def execute(self, inputs: Dict[str, Any]) -> ComponentResult:
        """Execute the output component"""
        try:
            response = inputs.get("response", "")
            query = inputs.get("query", "")
            
            if not response:
                return ComponentResult(
                    success=False,
                    error="No response provided for output component"
                )
            
            # Format the output
            formatted_output = self._format_output(query, response)
            
            # Prepare follow-up suggestions if enabled
            follow_up_suggestions = []
            if self.enable_follow_up:
                follow_up_suggestions = self._generate_follow_up_suggestions(query, response)
            
            return ComponentResult(
                success=True,
                data={
                    "formatted_response": formatted_output,
                    "query": query,
                    "response": response,
                    "timestamp": datetime.now().isoformat(),
                    "follow_up_suggestions": follow_up_suggestions,
                    "show_timestamps": self.show_timestamps
                },
                metadata={
                    "component_type": "output",
                    "component_id": self.component_id,
                    "response_length": len(response)
                }
            )
            
        except Exception as e:
            return ComponentResult(
                success=False,
                error=f"Error in output component: {str(e)}"
            )
    
    def _format_output(self, query: str, response: str) -> str:
        """Format the output for display"""
        formatted_parts = []
        
        if self.show_timestamps:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_parts.append(f"[{timestamp}]")
        
        formatted_parts.append(f"Q: {query}")
        formatted_parts.append(f"A: {response}")
        
        return "\n".join(formatted_parts)
    
    def _generate_follow_up_suggestions(self, query: str, response: str) -> list[str]:
        """Generate follow-up question suggestions"""
        suggestions = []
        
        # Simple follow-up suggestions based on response content
        if "document" in response.lower() or "file" in response.lower():
            suggestions.append("Can you provide more details about this document?")
            suggestions.append("Are there other related documents?")
        
        if "process" in response.lower() or "workflow" in response.lower():
            suggestions.append("How can I modify this workflow?")
            suggestions.append("What are the next steps?")
        
        if "data" in response.lower() or "information" in response.lower():
            suggestions.append("Can you analyze this data further?")
            suggestions.append("What insights can you provide?")
        
        # Generic suggestions
        if len(suggestions) < 3:
            suggestions.extend([
                "Can you explain this in more detail?",
                "What are the alternatives?",
                "How does this compare to other approaches?"
            ])
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def validate_config(self) -> bool:
        """Validate component configuration"""
        return (
            isinstance(self.show_timestamps, bool) and
            isinstance(self.enable_follow_up, bool) and
            isinstance(self.max_history, int) and
            self.max_history > 0
        )
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the expected input schema"""
        return {
            "response": {
                "type": "string",
                "description": "LLM generated response",
                "required": True
            },
            "query": {
                "type": "string",
                "description": "Original user query",
                "required": True
            }
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema"""
        return {
            "formatted_response": {
                "type": "string",
                "description": "Formatted response for display"
            },
            "query": {
                "type": "string",
                "description": "Original user query"
            },
            "response": {
                "type": "string",
                "description": "Raw LLM response"
            },
            "timestamp": {
                "type": "string",
                "description": "Response timestamp"
            },
            "follow_up_suggestions": {
                "type": "array",
                "description": "Suggested follow-up questions"
            }
        }
    
    def get_required_inputs(self) -> list[str]:
        """Get required input keys"""
        return ["response", "query"]
    
    def get_optional_inputs(self) -> list[str]:
        """Get optional input keys"""
        return []
