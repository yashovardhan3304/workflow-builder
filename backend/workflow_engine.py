from typing import Dict, Any, List, Optional
from components.factory import ComponentFactory
from components.base import BaseComponent, ComponentResult
import networkx as nx
from datetime import datetime

class WorkflowEngine:
    """Engine for executing workflows based on component connections"""
    
    def __init__(self):
        self.execution_log = []
    
    async def execute_workflow(self, workflow_data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Execute a workflow with the given query"""
        try:
            nodes = workflow_data.get("nodes", [])
            edges = workflow_data.get("edges", [])
            
            # Validate workflow structure
            is_valid, reason = self._validate_workflow_with_reason(nodes, edges)
            if not is_valid:
                raise ValueError(f"Invalid workflow structure: {reason}")
            
            # Build execution graph
            execution_graph = self._build_execution_graph(nodes, edges)
            
            # Execute workflow
            results = await self._execute_workflow_graph(execution_graph, query)
            
            # Log execution
            self._log_execution(workflow_data.get("id"), query, results)
            
            return {
                "success": True,
                "results": results,
                "execution_log": self.execution_log[-1] if self.execution_log else None
            }
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            self._log_execution_error(workflow_data.get("id"), query, error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "execution_log": self.execution_log[-1] if self.execution_log else None
            }
    
    def _validate_workflow_with_reason(self, nodes: List[Dict], edges: List[Dict]) -> (bool, str):
        """Validate workflow structure and return (is_valid, reason) when invalid"""
        if not nodes:
            return False, "No nodes present"
        if not edges:
            return False, "No connections present"
        
        # Check for required components
        component_types = [node.get("data", {}).get("type") for node in nodes]
        if "user_query" not in component_types:
            return False, "Missing required node: user_query"
        if "output" not in component_types:
            return False, "Missing required node: output"
        
        # Check for cycles
        try:
            graph = nx.DiGraph()
            for edge in edges:
                graph.add_edge(edge["source"], edge["target"])
            if not nx.is_directed_acyclic_graph(graph):
                return False, "Workflow contains cycles"
        except Exception as e:
            return False, f"Invalid edges: {str(e)}"
        
        return True, ""

    # Backwards compatibility alias (if called elsewhere)
    def _validate_workflow(self, nodes: List[Dict], edges: List[Dict]) -> bool:
        valid, _ = self._validate_workflow_with_reason(nodes, edges)
        return valid
    
    def _build_execution_graph(self, nodes: List[Dict], edges: List[Dict]) -> nx.DiGraph:
        """Build execution graph from workflow data"""
        graph = nx.DiGraph()
        
        # Add nodes
        for node in nodes:
            node_id = node["id"]
            node_data = node.get("data", {})
            graph.add_node(node_id, **node_data)
        
        # Add edges
        for edge in edges:
            graph.add_edge(edge["source"], edge["target"])
        
        return graph
    
    async def _execute_workflow_graph(self, graph: nx.DiGraph, query: str) -> Dict[str, Any]:
        """Execute the workflow graph"""
        results = {}
        execution_order = list(nx.topological_sort(graph))
        
        for node_id in execution_order:
            node_data = graph.nodes[node_id]
            component_type = node_data.get("type")
            
            if not component_type:
                continue
            
            # Create component instance
            component = ComponentFactory.create_component(
                component_type=component_type,
                component_id=node_id,
                config=node_data.get("config", {})
            )
            
            # Prepare inputs
            inputs = self._prepare_component_inputs(node_id, graph, results, query)
            
            # Execute component
            result = await component.execute(inputs)
            
            if not result.success:
                raise Exception(f"Component {node_id} failed: {result.error}")
            
            # Store result
            results[node_id] = result.data
            
            # Update graph with result
            graph.nodes[node_id]["result"] = result.data
        
        return results
    
    def _prepare_component_inputs(self, node_id: str, graph: nx.DiGraph, results: Dict, query: str) -> Dict[str, Any]:
        """Prepare inputs for a component based on incoming edges and results"""
        inputs = {}
        
        # Add query for user_query component
        if graph.nodes[node_id].get("type") == "user_query":
            inputs["query"] = query
            inputs["timestamp"] = datetime.now().isoformat()
            return inputs
        
        # Get inputs from incoming edges
        for source_id in graph.predecessors(node_id):
            source_result = results.get(source_id, {})
            source_type = graph.nodes[source_id].get("type")
            
            # Map outputs to inputs based on component types
            if source_type == "user_query":
                inputs["query"] = source_result.get("query", "")
            elif source_type == "knowledge_base":
                inputs["query"] = source_result.get("query", "")
                inputs["context"] = source_result.get("context", "")
            elif source_type == "llm_engine":
                inputs["query"] = source_result.get("query", "")
                inputs["response"] = source_result.get("response", "")
        
        return inputs
    
    def _log_execution(self, workflow_id: Optional[str], query: str, results: Dict[str, Any]):
        """Log successful workflow execution"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "workflow_id": workflow_id,
            "query": query,
            "status": "completed",
            "results": results,
            "error": None
        }
        self.execution_log.append(log_entry)
    
    def _log_execution_error(self, workflow_id: Optional[str], query: str, error: str):
        """Log workflow execution error"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "workflow_id": workflow_id,
            "query": query,
            "status": "failed",
            "results": None,
            "error": error
        }
        self.execution_log.append(log_entry)
    
    def get_execution_log(self, limit: int = 100) -> List[Dict]:
        """Get recent execution logs"""
        return self.execution_log[-limit:] if self.execution_log else []
    
    def clear_execution_log(self):
        """Clear execution log"""
        self.execution_log.clear()
