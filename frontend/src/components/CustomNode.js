import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { COMPONENT_METADATA } from '../types';

const CustomNode = memo(({ id, data, selected }) => {
  const metadata = COMPONENT_METADATA[data.type] || {};
  
  const getNodeColor = (type) => {
    switch (type) {
      case 'user_query':
        return 'bg-blue-500';
      case 'knowledge_base':
        return 'bg-green-500';
      case 'llm_engine':
        return 'bg-purple-500';
      case 'output':
        return 'bg-orange-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getNodeBorderColor = (type) => {
    switch (type) {
      case 'user_query':
        return 'border-blue-200';
      case 'knowledge_base':
        return 'border-green-200';
      case 'llm_engine':
        return 'border-purple-200';
      case 'output':
        return 'border-orange-200';
      default:
        return 'border-gray-200';
    }
  };

  return (
    <div
      className={`
        relative bg-white border-2 rounded-lg shadow-sm p-4 min-w-[200px]
        ${getNodeBorderColor(data.type)}
        ${selected ? 'ring-2 ring-primary-500 ring-offset-2' : ''}
        transition-all duration-200 hover:shadow-md
      `}
    >
      {/* Input Handle */}
      {data.type !== 'user_query' && (
        <>
          <Handle
            type="target"
            position={Position.Left}
            className="w-6 h-6 bg-gray-500 border-2 border-white rounded-full shadow"
          />
          <div className="absolute -left-8 top-1/2 -translate-y-1/2 text-[10px] text-gray-600 select-none pointer-events-none">
            In
          </div>
        </>
      )}

      {/* Node Header */}
      <div className="flex items-center space-x-3 mb-3">
        <div className={`w-3 h-3 rounded-full ${getNodeColor(data.type)}`} />
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-gray-900 truncate">
            {data.label || metadata.label}
          </h3>
          <p className="text-xs text-gray-500">
            {metadata.description}
          </p>
        </div>
        {data.onDelete && (
          <button
            onClick={(e) => { e.stopPropagation(); data.onDelete?.(id); }}
            className="text-xs text-red-600 hover:text-red-700 border border-red-200 px-2 py-0.5 rounded"
            title="Delete node"
          >
            Delete
          </button>
        )}
      </div>

      {/* Node Content */}
      <div className="text-xs text-gray-600">
        {data.type === 'output' ? (
          <div className="mt-2">
            <div className="text-xs text-gray-500 mb-1">Final Output</div>
            <div className="border border-gray-200 rounded p-2 bg-gray-50 max-h-40 overflow-auto text-[11px] whitespace-pre-wrap">
              {data.result?.formatted_response || 'Connect components into this Output to view results.'}
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="font-medium">Type:</span>
              <span className="text-gray-500">{data.type}</span>
            </div>
            {data.config && Object.keys(data.config).length > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-100">
                <span className="font-medium">Config:</span>
                <div className="mt-1 space-y-1">
                  {Object.entries(data.config).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-xs">
                      <span className="text-gray-500">{key}:</span>
                      <span className="text-gray-700 font-mono">
                        {typeof value === 'boolean' ? (value ? '✓' : '✗') : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}


            {data.type === 'knowledge_base' && (
              <div className="mt-2 pt-2 border-t border-gray-100 space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs text-gray-600 mr-2">Collection (KB)</label>
                  <input
                    type="text"
                    className="border rounded px-2 py-1 text-xs w-40"
                    placeholder="default"
                    value={data.config?.collection_name || ''}
                    onChange={(e) => data.onUpdateConfig?.(id, { collection_name: e.target.value })}
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Output Handle */}
      {data.type !== 'output' && (
        <>
          <Handle
            type="source"
            position={Position.Right}
            className="w-6 h-6 bg-gray-500 border-2 border-white rounded-full shadow"
          />
          <div className="absolute -right-8 top-1/2 -translate-y-1/2 text-[10px] text-gray-600 select-none pointer-events-none">
            Out
          </div>
        </>
      )}

      {/* Node ID (for debugging) */}
      <div className="absolute top-1 right-1">
        <span className="text-xs text-gray-400 font-mono">
          {id.split('_')[0]}
        </span>
      </div>
    </div>
  );
});

CustomNode.displayName = 'CustomNode';

export default CustomNode;
