from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

class ComponentConfig(BaseModel):
    """Base configuration for all components"""
    component_type: str
    component_id: str
    config: Dict[str, Any] = {}

class ComponentResult(BaseModel):
    """Result from component execution"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseComponent(ABC):
    """Base class for all workflow components"""
    
    def __init__(self, config: ComponentConfig):
        self.config = config
        self.component_type = config.component_type
        self.component_id = config.component_id
    
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> ComponentResult:
        """Execute the component with given inputs"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate component configuration"""
        pass
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the expected input schema for this component"""
        return {}
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema for this component"""
        return {}
    
    def get_required_inputs(self) -> list[str]:
        """Get list of required input keys"""
        return []
    
    def get_optional_inputs(self) -> list[str]:
        """Get list of optional input keys"""
        return []
