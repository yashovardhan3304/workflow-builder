import google.generativeai as genai
import requests
from typing import Dict, Any, Optional
from .base import BaseComponent, ComponentConfig, ComponentResult
from config import settings

class LLMEngineComponent(BaseComponent):
    """Component for LLM interactions with Gemini"""
    
    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        self.model = config.config.get("model", "gemini-1.5-flash")
        self.temperature = config.config.get("temperature", 0.7)
        self.max_tokens = config.config.get("max_tokens", 1000)
        self.use_web_search = config.config.get("use_web_search", False)
        self.custom_prompt = config.config.get("custom_prompt", None)
        
        # Initialize Gemini client
        if settings.google_api_key:
            try:
                genai.configure(api_key=settings.google_api_key)
            except Exception:
                pass
    
    async def execute(self, inputs: Dict[str, Any]) -> ComponentResult:
        """Execute the LLM engine component"""
        try:
            query = inputs.get("query", "")
            context = inputs.get("context", "")
            
            if not query:
                return ComponentResult(
                    success=False,
                    error="No query provided for LLM engine"
                )
            
            # Perform web search if enabled
            web_results = ""
            if self.use_web_search:
                web_results = await self._perform_web_search(query)
            
            # Build the prompt
            prompt = self._build_prompt(query, context, web_results)
            
            # Generate response from LLM
            response = await self._generate_llm_response(prompt)
            
            return ComponentResult(
                success=True,
                data={
                    "response": response,
                    "query": query,
                    "context_used": bool(context),
                    "web_search_used": self.use_web_search,
                    "model": self.model,
                    "web_results": web_results if self.use_web_search else None
                },
                metadata={
                    "component_type": "llm_engine",
                    "component_id": self.component_id,
                    "model": self.model,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
            )
            
        except Exception as e:
            return ComponentResult(
                success=False,
                error=f"Error in LLM engine component: {str(e)}"
            )
    
    def _build_prompt(self, query: str, context: str, web_results: str) -> str:
        """Build the prompt for the LLM"""
        prompt_parts = []
        
        if self.custom_prompt:
            prompt_parts.append(self.custom_prompt)
        
        if context:
            prompt_parts.append(f"Context from documents:\n{context}")
        
        if web_results:
            prompt_parts.append(f"Recent web information:\n{web_results}")
        
        prompt_parts.append(f"User question: {query}")
        prompt_parts.append("Please provide a comprehensive and accurate answer based on the available information.")
        
        return "\n\n".join(prompt_parts)
    
    async def _generate_llm_response(self, prompt: str) -> str:
        """Generate response from Gemini"""
        if not settings.google_api_key:
            return f"(Mock) Generated answer for:\n{prompt[:500]}\n\nNote: No Google API key configured; returning a local mock response."
        return await self._generate_gemini_response(prompt)
    
    async def _generate_gemini_response(self, prompt: str) -> str:
        """Generate response using Gemini with model fallbacks"""
        try:
            if not settings.google_api_key:
                return f"(Mock) Generated answer for:\n{prompt[:500]}\n\nNote: No Google API key configured; returning a local mock response."

            # Configure with the environment key
            genai.configure(api_key=settings.google_api_key)

            # Try the configured model, then fallbacks commonly available
            candidate_models = [
                self.model,
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-pro"
            ]

            last_error = None
            for model_name in candidate_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    return getattr(response, "text", "") or ""
                except Exception as inner_e:
                    last_error = inner_e
                    continue

            raise Exception(str(last_error) if last_error else "Unknown Gemini error")
        except Exception as e:
            msg = str(e)
            if "invalid" in msg.lower() or "api key" in msg.lower():
                return f"(Mock) Gemini key invalid. Set GOOGLE_API_KEY in backend .env.\n\n{prompt[:800]}"
            if "quota" in msg.lower() or "429" in msg:
                return f"(Mock) Gemini quota exceeded. Check billing or reduce usage.\n\n{prompt[:800]}"
            raise Exception(f"Gemini API error: {msg}")
    
    async def _perform_web_search(self, query: str) -> str:
        """Perform web search using SerpAPI"""
        if not settings.serpapi_api_key:
            return "Web search not available (no API key configured)"
        
        try:
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": settings.serpapi_api_key,
                "num": 3  # Limit to 3 results
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("organic_results", [])
            
            if not results:
                return "No recent web results found"
            
            # Extract and format search results
            formatted_results = []
            for result in results[:3]:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                if title and snippet:
                    formatted_results.append(f"Title: {title}\nSummary: {snippet}")
            
            return "\n\n".join(formatted_results)
            
        except Exception as e:
            return f"Web search error: {str(e)}"
    
    def validate_config(self) -> bool:
        """Validate component configuration"""
        return (
            isinstance(self.model, str) and
            isinstance(self.temperature, (int, float)) and
            0 <= self.temperature <= 2 and
            isinstance(self.max_tokens, int) and
            self.max_tokens > 0 and
            isinstance(self.use_web_search, bool)
        )
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the expected input schema"""
        return {
            "query": {
                "type": "string",
                "description": "User's question for the LLM",
                "required": True
            },
            "context": {
                "type": "string",
                "description": "Context from knowledge base",
                "required": False
            }
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema"""
        return {
            "response": {
                "type": "string",
                "description": "LLM generated response"
            },
            "query": {
                "type": "string",
                "description": "Original user query"
            },
            "context_used": {
                "type": "boolean",
                "description": "Whether context was used"
            },
            "web_search_used": {
                "type": "boolean",
                "description": "Whether web search was performed"
            },
            "model": {
                "type": "string",
                "description": "LLM model used"
            }
        }
    
    def get_required_inputs(self) -> list[str]:
        """Get required input keys"""
        return ["query"]
    
    def get_optional_inputs(self) -> list[str]:
        """Get optional input keys"""
        return ["context"]
