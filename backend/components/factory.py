from typing import Dict, Any
from .base import BaseComponent, ComponentConfig
from .user_query import UserQueryComponent
from .knowledge_base import KnowledgeBaseComponent
from .llm_engine import LLMEngineComponent
from .output import OutputComponent

class ComponentFactory:
    """Factory for creating workflow components"""
    
    _component_registry = {
        "user_query": UserQueryComponent,
        "knowledge_base": KnowledgeBaseComponent,
        "llm_engine": LLMEngineComponent,
        "output": OutputComponent
    }
    
    @classmethod
    def create_component(cls, component_type: str, component_id: str, config: Dict[str, Any] = None) -> BaseComponent:
        """Create a component instance"""
        if component_type not in cls._component_registry:
            raise ValueError(f"Unknown component type: {component_type}")
        
        if config is None:
            config = {}
        
        component_config = ComponentConfig(
            component_type=component_type,
            component_id=component_id,
            config=config
        )
        
        component_class = cls._component_registry[component_type]
        return component_class(component_config)
    
    @classmethod
    def get_available_components(cls) -> list[str]:
        """Get list of available component types"""
        return list(cls._component_registry.keys())
    
    @classmethod
    def get_component_schema(cls, component_type: str) -> Dict[str, Any]:
        """Get the configuration schema for a component type"""
        if component_type not in cls._component_registry:
            raise ValueError(f"Unknown component type: {component_type}")
        
        # Create a temporary instance to get the schema
        temp_component = cls.create_component(component_type, "temp", {})
        
        return {
            "input_schema": temp_component.get_input_schema(),
            "output_schema": temp_component.get_output_schema(),
            "required_inputs": temp_component.get_required_inputs(),
            "optional_inputs": temp_component.get_optional_inputs()
        }
    
    @classmethod
    def validate_component_config(cls, component_type: str, config: Dict[str, Any]) -> bool:
        """Validate component configuration"""
        if component_type not in cls._component_registry:
            return False
        
        try:
            temp_component = cls.create_component(component_type, "temp", config)
            return temp_component.validate_config()
        except Exception:
            return False
