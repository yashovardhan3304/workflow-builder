import React, { useCallback, useEffect, useRef, useState } from 'react';
import ReactFlow, {
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  useReactFlow,
  ReactFlowProvider,
  ConnectionMode
} from 'reactflow';
import 'reactflow/dist/style.css';

import CustomNode from './CustomNode';
import { UI_CONSTANTS } from '../types';

const nodeTypes = {
  custom: CustomNode,
};

const WorkflowCanvas = ({ onWorkflowChange, selectedNode, onNodeSelect, connectMode = false, workflow }) => {
  const reactFlowWrapper = useRef(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const { screenToFlowPosition } = useReactFlow();

  // Sync canvas with external workflow (e.g., after Load or Save)
  useEffect(() => {
    if (!workflow) return;
    const incomingNodes = Array.isArray(workflow.nodes) ? workflow.nodes : [];
    const incomingEdges = Array.isArray(workflow.edges) ? workflow.edges : [];

    // Skip if identical by ids/length
    const sameNodeSet = nodes.length === incomingNodes.length &&
      nodes.every((n, i) => n.id === (incomingNodes[i] && incomingNodes[i].id));
    const sameEdgeSet = edges.length === incomingEdges.length &&
      edges.every((e, i) => e.id === (incomingEdges[i] && incomingEdges[i].id));
    if (sameNodeSet && sameEdgeSet) return;

    // Rehydrate nodes: ensure each has required shape and attach UI-only helpers
    const hydratedNodes = incomingNodes.map((n) => {
      const id = n.id;
      return {
        ...n,
        id,
        type: n.type || 'custom',
        data: {
          ...(n.data || {}),
          onDelete: (nodeId) => {
            setEdges((eds) => {
              const filtered = eds.filter((e) => e.source !== nodeId && e.target !== nodeId);
              return filtered;
            });
            setNodes((nds) => {
              const updated = nds.filter((node) => node.id !== nodeId);
              // Update parent workflow after state change
              onWorkflowChange({ nodes: sanitizeNodes(updated), edges });
              return updated;
            });
          },
          onUpdateConfig: (nodeId, newConfig) => {
            setNodes((nds) => {
              const updated = nds.map((node) =>
                node.id === nodeId
                  ? { ...node, data: { ...(node.data || {}), config: { ...(node.data?.config || {}), ...newConfig } } }
                  : node
              );
              onWorkflowChange({ nodes: sanitizeNodes(updated), edges });
              return updated;
            });
          },
        },
      };
    });

    setNodes(hydratedNodes);
    setEdges(incomingEdges);
  }, [workflow, nodes, edges, setNodes, setEdges]);

  const sanitizeNodes = useCallback((ns) => {
    // Remove non-serializable props (functions) from node data before lifting state
    return ns.map((n) => ({
      ...n,
      data: {
        ...(n.data || {}),
        onDelete: undefined,
        onUpdateConfig: undefined,
      },
    }));
  }, []);

  const onConnect = useCallback(
    (params) => {
      setEdges((eds) => {
        const updated = addEdge({ ...params, type: 'smoothstep', animated: true }, eds);
        onWorkflowChange({ nodes: sanitizeNodes(nodes), edges: updated });
        return updated;
      });
    },
    [nodes, onWorkflowChange, sanitizeNodes]
  );

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      const componentType = event.dataTransfer.getData('componentType');
      const componentData = JSON.parse(event.dataTransfer.getData('componentData'));

      if (typeof type === 'undefined' || !type) {
        return;
      }

      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newId = `${componentType}_${Date.now()}`;
      const newNode = {
        id: newId,
        type: 'custom',
        position,
        data: {
          label: componentData.label,
          type: componentType,
          config: componentData.defaultConfig || {},
          ...componentData,
          onDelete: (id) => {
            setEdges((eds) => eds.filter((e) => e.source !== id && e.target !== id));
            setNodes((nds) => nds.filter((n) => n.id !== id));
            const updatedNodes = nodes.filter((n) => n.id !== id);
            const updatedEdges = edges.filter((e) => e.source !== id && e.target !== id);
            onWorkflowChange({ nodes: updatedNodes, edges: updatedEdges });
          },
          onUpdateConfig: (nodeId, newConfig) => {
            setNodes((nds) => {
              const updated = nds.map((node) =>
                node.id === nodeId
                  ? { ...node, data: { ...(node.data || {}), config: { ...(node.data?.config || {}), ...newConfig } } }
                  : node
              );
              onWorkflowChange({ nodes: sanitizeNodes(updated), edges });
              return updated;
            });
          },
          result: componentType === 'output' ? { formatted_response: '' } : undefined
        },
      };

      setNodes((nds) => nds.concat(newNode));
      onWorkflowChange({ nodes: sanitizeNodes([...nodes, newNode]), edges });
    },
    [screenToFlowPosition, setNodes, nodes, edges, onWorkflowChange, sanitizeNodes]
  );

  const connectFromRef = useRef(null);

  const onNodeClick = useCallback((event, node) => {
    if (connectMode) {
      event.preventDefault();
      event.stopPropagation();
      if (!connectFromRef.current) {
        connectFromRef.current = node.id;
      } else if (connectFromRef.current && connectFromRef.current !== node.id) {
        const newEdge = { id: `${connectFromRef.current}-${node.id}-${Date.now()}`, source: connectFromRef.current, target: node.id };
        setEdges((eds) => addEdge(newEdge, eds));
        onWorkflowChange({ nodes, edges: [...edges, newEdge] });
        connectFromRef.current = null;
      }
      return;
    }
    onNodeSelect(node.id);
  }, [connectMode, onNodeSelect, setEdges, nodes, edges, onWorkflowChange]);

  const onPaneClick = useCallback(() => {
    if (connectMode) {
      connectFromRef.current = null;
      return;
    }
    onNodeSelect(null);
  }, [onNodeSelect]);

  const onNodesDelete = useCallback((deleted) => {
    const deletedNodeIds = deleted.map(node => node.id);
    setEdges((eds) => eds.filter(edge => 
      !deletedNodeIds.includes(edge.source) && !deletedNodeIds.includes(edge.target)
    ));
    const updatedNodes = nodes.filter(node => !deletedNodeIds.includes(node.id));
    onWorkflowChange({ nodes: sanitizeNodes(updatedNodes), edges });
  }, [setEdges, nodes, edges, onWorkflowChange, sanitizeNodes]);

  const onEdgesDelete = useCallback((deleted) => {
    onWorkflowChange({ nodes: sanitizeNodes(nodes), edges: edges.filter(edge => !deleted.some(d => d.id === edge.id)) });
  }, [nodes, edges, onWorkflowChange, sanitizeNodes]);

  const onEdgeClick = useCallback((event, edge) => {
    event.stopPropagation();
    const updated = edges.filter((e) => e.id !== edge.id);
    setEdges(updated);
    onWorkflowChange({ nodes: sanitizeNodes(nodes), edges: updated });
  }, [edges, nodes, setEdges, onWorkflowChange, sanitizeNodes]);

  // Note: parent workflow is updated explicitly in event handlers to avoid feedback loops that can cause jitter

  return (
    <div className="h-full w-full relative" ref={reactFlowWrapper}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onInit={setReactFlowInstance}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        onNodesDelete={onNodesDelete}
        onEdgesDelete={onEdgesDelete}
        onEdgeClick={onEdgeClick}
        nodeTypes={nodeTypes}
        connectOnClick
        connectionMode={ConnectionMode.Loose}
        connectionRadius={30}
        connectionLineType="smoothstep"
        connectionLineStyle={{ stroke: '#3b82f6', strokeWidth: 2 }}
        elementsSelectable
        nodesDraggable
        nodesConnectable
        fitView
        attributionPosition="bottom-left"
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{
          type: 'smoothstep',
          animated: true,
          style: { stroke: '#3b82f6', strokeWidth: 2 },
          markerEnd: {
            type: 'arrowclosed',
            width: 16,
            height: 16,
            color: '#3b82f6'
          }
        }}
      >
        <Controls position="top-left" showInteractive={false} />
        <Background color="#e5e7eb" gap={24} />
        <MiniMap
          style={{
            height: UI_CONSTANTS.MINIMAP_SIZE,
            width: UI_CONSTANTS.MINIMAP_SIZE,
          }}
          zoomable
          pannable
        />
      </ReactFlow>
    </div>
  );
};

const WorkflowCanvasWrapper = (props) => (
  <ReactFlowProvider>
    <WorkflowCanvas {...props} />
  </ReactFlowProvider>
);

export default WorkflowCanvasWrapper;
