import React, { useState, useCallback } from 'react';
import { COMPONENT_METADATA, DEFAULT_COMPONENT_CONFIGS } from './types';
import ComponentLibrary from './components/ComponentLibrary';
import WorkflowCanvas from './components/WorkflowCanvas';
import { Save, Play, Settings, FileText, MessageSquare, List, Send } from 'lucide-react';
import { createWorkflow, getWorkflows, getWorkflow, chatWithWorkflow, getCollections } from './services/api';

const App = () => {
  const [workflow, setWorkflow] = useState({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [activeTab, setActiveTab] = useState('builder');
  const [workflowName, setWorkflowName] = useState('Untitled Workflow');
  const [savedWorkflows, setSavedWorkflows] = useState([]);
  const [loadingWorkflows, setLoadingWorkflows] = useState(false);
  const [currentWorkflowId, setCurrentWorkflowId] = useState(null);
  const [chatInput, setChatInput] = useState('');
  const [chatOutput, setChatOutput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [collectionName, setCollectionName] = useState('default');
  const [collections, setCollections] = useState([]);

  const handleDragStart = useCallback((event, type, metadata) => {
    try {
      const payload = {
        ...metadata,
        defaultConfig: DEFAULT_COMPONENT_CONFIGS[type] || {}
      };
      // Required by React Flow HTML5 DnD examples
      event.dataTransfer.setData('application/reactflow', 'custom');
      // Custom data for our drop handler
      event.dataTransfer.setData('componentType', type);
      event.dataTransfer.setData('componentData', JSON.stringify(payload));
      // Improve compatibility
      event.dataTransfer.setData('text/plain', type);
      event.dataTransfer.effectAllowed = 'move';
    } catch (e) {
      // noop
    }
  }, []);

  const handleWorkflowChange = useCallback((newWorkflow) => {
    setWorkflow(newWorkflow);
  }, []);

  const handleNodeSelect = useCallback((nodeId) => {
    setSelectedNode(nodeId);
  }, []);

  const handleSaveWorkflow = useCallback(async () => {
    try {
      const name = (workflowName || '').trim();
      if (!name) {
        alert('Please enter a workflow name first.');
        return;
      }
      const payload = {
        name,
        description: '',
        nodes: workflow.nodes,
        edges: workflow.edges,
      };
      const res = await createWorkflow(payload);
      if (res.success) {
        alert('Workflow saved successfully');
        setCurrentWorkflowId(res.data.id);
      } else {
        alert(`Save failed: ${res.error}`);
      }
    } catch (error) {
      console.error('Error saving workflow:', error);
      alert('Error saving workflow');
    }
  }, [workflow, workflowName]);

  const handleExecuteWorkflow = useCallback(async () => {
    try {
      setActiveTab('chat');
    } catch (error) {
      console.error('Error executing workflow:', error);
      alert('Error executing workflow');
    }
  }, [workflow]);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'builder':
        return (
          <div className="flex h-full">
            <div className="w-80 flex-shrink-0">
              <ComponentLibrary onDragStart={handleDragStart} />
            </div>
            <div className="flex-1">
              <WorkflowCanvas
                onWorkflowChange={handleWorkflowChange}
                selectedNode={selectedNode}
                onNodeSelect={handleNodeSelect}
                workflow={workflow}
              />
            </div>
          </div>
        );
      case 'workflows':
        return (
          <div className="h-full p-6 overflow-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Saved Workflows</h3>
              <button
                onClick={async () => {
                  setLoadingWorkflows(true);
                  const res = await getWorkflows();
                  if (res.success) setSavedWorkflows(res.data);
                  setLoadingWorkflows(false);
                }}
                className="btn-primary flex items-center space-x-2"
              >
                <List className="w-4 h-4" />
                <span>Refresh</span>
              </button>
            </div>
            {loadingWorkflows ? (
              <div className="text-gray-500">Loading…</div>
            ) : (
              <ul className="space-y-2">
                {savedWorkflows.map(w => (
                  <li key={w.id} className="flex items-center justify-between bg-white border rounded p-3">
                    <div>
                      <div className="font-medium">{w.name}</div>
                      <div className="text-xs text-gray-500">ID: {w.id}</div>
                    </div>
                    <button
                      className="btn-primary"
                      onClick={async () => {
                        const res = await getWorkflow(w.id);
                        if (res.success) {
                          setActiveTab('builder');
                          setWorkflow({ nodes: res.data.nodes || [], edges: res.data.edges || [] });
                        }
                      }}
                    >
                      Load
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      case 'chat':
        return (
          <div className="h-full flex flex-col p-6 space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Execute Workflow</h3>
              <p className="text-sm text-gray-600">Enter a query and run it against the current workflow.</p>
            </div>
            <div className="flex items-center space-x-2">
              <input
                className="flex-1 border rounded px-3 py-2 focus:outline-none focus:ring"
                placeholder="Ask something..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
              />
              <button
                className="btn-primary flex items-center space-x-2"
                disabled={chatLoading || !chatInput}
                onClick={async () => {
                  try {
                    setChatLoading(true);
                    // quick client-side validation to avoid backend 500s
                    const hasNodes = Array.isArray(workflow.nodes) && workflow.nodes.length > 0;
                    const hasEdges = Array.isArray(workflow.edges) && workflow.edges.length > 0;
                    const hasUserQuery = (workflow.nodes || []).some(n => n?.data?.type === 'user_query');
                    const hasOutput = (workflow.nodes || []).some(n => n?.data?.type === 'output');
                    if (!hasNodes || !hasEdges || !hasUserQuery || !hasOutput) {
                      setChatOutput('Error: Workflow must include user_query and output nodes and at least one connection.');
                      return;
                    }
                    let workflowId = currentWorkflowId;
                    if (!workflowId) {
                      const temp = await createWorkflow({
                        name: `Temp ${new Date().toISOString()}`,
                        description: '',
                        nodes: workflow.nodes,
                        edges: workflow.edges,
                      });
                      if (!temp.success) throw new Error(temp.error || 'Failed to create workflow');
                      workflowId = temp.data.id;
                      setCurrentWorkflowId(workflowId);
                    }
                    const res = await chatWithWorkflow({ workflow_id: workflowId, query: chatInput });
                    if (res.success) {
                      const responseText = res.data.response || '';
                      setChatOutput(responseText);
                      // Update Output node content in builder view
                      setWorkflow((prev) => {
                        const updatedNodes = prev.nodes.map((n) => {
                          if (n.data?.type === 'output') {
                            return {
                              ...n,
                              data: {
                                ...n.data,
                                result: { ...(n.data.result || {}), formatted_response: responseText },
                              },
                            };
                          }
                          return n;
                        });
                        return { ...prev, nodes: updatedNodes };
                      });
                    } else {
                      setChatOutput(`Error: ${res.error}`);
                    }
                  } catch (err) {
                    setChatOutput(`Error: ${err.message}`);
                  } finally {
                    setChatLoading(false);
                  }
                }}
              >
                <Send className="w-4 h-4" />
                <span>{chatLoading ? 'Running...' : 'Run'}</span>
              </button>
            </div>
            <div className="flex-1 flex flex-col min-h-0">
              <div className="text-sm text-gray-600 mb-1">Output</div>
              <div className="flex-1 border rounded p-3 bg-white overflow-y-auto whitespace-pre-wrap min-h-0">
                {chatOutput || 'No output yet.'}
              </div>
            </div>
          </div>
        );
      case 'documents':
        return (
          <div className="h-full p-6 space-y-6 overflow-auto">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Document Management</h3>
              <p className="text-sm text-gray-600">Upload PDFs to use as knowledge sources.</p>
            </div>
            <div className="card">
              <h4 className="text-sm font-medium text-gray-900 mb-3">Upload PDF</h4>
              <div className="flex items-center gap-3">
                <input id="pdf-file" type="file" accept="application/pdf" className="flex-1" />
                <input
                  className="border rounded px-2 py-1 text-sm"
                  placeholder="Collection name (default)"
                  value={collectionName}
                  onChange={(e) => setCollectionName(e.target.value)}
                />
                <button
                  className="btn-primary"
                  disabled={uploading}
                  onClick={async () => {
                    try {
                      setUploadError('');
                      setUploading(true);
                      const input = document.getElementById('pdf-file');
                      const file = input && input.files && input.files[0];
                      if (!file) { setUploadError('Please choose a PDF'); setUploading(false); return; }
                      const formData = new FormData();
                      formData.append('file', file);
                      if (collectionName) formData.append('collection_name', collectionName);
                      const res = await fetch((process.env.REACT_APP_API_URL || 'http://localhost:8000') + '/api/documents/upload', {
                        method: 'POST',
                        body: formData
                      });
                      if (!res.ok) throw new Error('Upload failed');
                      await res.json();
                      // refresh list
                      setDocsLoading(true);
                      try {
                        const listRes = await fetch((process.env.REACT_APP_API_URL || 'http://localhost:8000') + '/api/documents');
                        const data = await listRes.json();
                        setDocuments(data);
                      } finally {
                        setDocsLoading(false);
                      }
                      if (input) input.value = '';
                    } catch (e) {
                      setUploadError(e.message || 'Upload error');
                    } finally {
                      setUploading(false);
                    }
                  }}
                >{uploading ? 'Uploading...' : 'Upload'}</button>
              </div>
              {uploadError && <div className="text-sm text-red-600 mt-2">{uploadError}</div>}
            </div>
            <div className="card">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium text-gray-900">Uploaded Documents</h4>
                <div className="flex items-center gap-2">
                  <input
                    className="border rounded px-2 py-1 text-sm"
                    placeholder="Filter by collection"
                    value={collectionName}
                    onChange={(e) => setCollectionName(e.target.value)}
                  />
                  <button
                    className="btn-secondary"
                    onClick={async () => {
                      setDocsLoading(true);
                      try {
                        const base = (process.env.REACT_APP_API_URL || 'http://localhost:8000');
                        const url = collectionName ? `${base}/api/documents?collection=${encodeURIComponent(collectionName)}` : `${base}/api/documents`;
                        const res = await fetch(url);
                        const data = await res.json();
                        setDocuments(data);
                      } finally {
                        setDocsLoading(false);
                      }
                    }}
                  >Refresh</button>
                </div>
              </div>
              {docsLoading ? (
                <div className="text-gray-500">Loading…</div>
              ) : (
                <ul className="divide-y">
                  {documents.map((d) => (
                    <li key={d.id} className="py-2 flex items-center justify-between">
                      <div>
                        <div className="font-medium text-sm">{d.filename}</div>
                        <div className="text-xs text-gray-500">ID: {d.id} • {Math.round((d.file_size || 0)/1024)} KB</div>
                      </div>
                      <span className="text-xs text-gray-400">{d.file_type?.toUpperCase()}</span>
                    </li>
                  ))}
                  {documents.length === 0 && (
                    <li className="py-2 text-sm text-gray-500">No documents uploaded yet.</li>
                  )}
                </ul>
              )}
            </div>
          </div>
        );
      case 'workflows':
        return (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <Settings className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Workflow Management</h3>
              <p className="text-gray-600">Manage your saved workflows</p>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <input
              className="text-2xl font-bold text-gray-900 bg-transparent border-b border-gray-200 focus:outline-none focus:border-primary-500"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              placeholder="Name this workflow"
            />
            <div className="flex items-center space-x-2">
              <button
                onClick={handleSaveWorkflow}
                className="btn-primary flex items-center space-x-2"
                disabled={workflow.nodes.length === 0}
              >
                <Save className="w-4 h-4" />
                <span>Save</span>
              </button>
              <button
                onClick={handleExecuteWorkflow}
                className="btn-primary flex items-center space-x-2"
                disabled={workflow.nodes.length === 0}
              >
                <Play className="w-4 h-4" />
                <span>Execute</span>
              </button>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">
              {workflow.nodes.length} nodes, {workflow.edges.length} connections
            </span>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-gray-200 px-6">
        <div className="flex space-x-8">
          {[
            { id: 'builder', label: 'Workflow Builder', icon: Settings },
            { id: 'chat', label: 'Chat', icon: MessageSquare },
            { id: 'documents', label: 'Documents', icon: FileText },
            { id: 'workflows', label: 'Workflows', icon: Settings }
          ].map((tab) => {
            const IconComponent = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm
                  ${activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <IconComponent className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden relative">
        {renderTabContent()}
        {/* Floating Run button only */}
        {activeTab === 'builder' && (
          <button
            onClick={handleExecuteWorkflow}
            className={`fixed bottom-6 right-6 rounded-full shadow-lg px-5 py-3 flex items-center space-x-2 ${workflow.nodes.length === 0 ? 'bg-gray-300 cursor-not-allowed' : 'bg-primary-600 hover:bg-primary-700 text-white'}`}
            disabled={workflow.nodes.length === 0}
            title={workflow.nodes.length === 0 ? 'Add nodes to run' : 'Run'}
          >
            <Play className="w-4 h-4" />
            <span>Run</span>
          </button>
        )}
      </main>

      {/* Status Bar */}
      <footer className="bg-white border-t border-gray-200 px-6 py-2">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>Ready to build amazing workflows</span>
          <span>v1.0.0</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
