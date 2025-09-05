import React from 'react';
import { COMPONENT_METADATA, COMPONENT_CATEGORIES } from '../types';
import { MessageSquare, Database, Brain, Monitor } from 'lucide-react';

const ComponentLibrary = ({ onDragStart }) => {
  const iconMap = {
    MessageSquare,
    Database,
    Brain,
    Monitor
  };

  const renderComponent = (type, metadata) => {
    const IconComponent = iconMap[metadata.icon];
    
    return (
      <div
        key={type}
        className="bg-white border border-gray-200 rounded-lg p-4 mb-3 cursor-move hover:shadow-md transition-shadow duration-200"
        draggable
        onDragStart={(e) => onDragStart(e, type, metadata)}
      >
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0">
            <IconComponent className="w-6 h-6 text-primary-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-medium text-gray-900 truncate">
              {metadata.label}
            </h3>
            <p className="text-xs text-gray-500 mt-1">
              {metadata.description}
            </p>
          </div>
        </div>
      </div>
    );
  };

  const renderCategory = (category, title) => {
    const components = Object.entries(COMPONENT_METADATA).filter(
      ([_, metadata]) => metadata.category === category
    );

    if (components.length === 0) return null;

    return (
      <div key={category} className="mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
          {title}
        </h3>
        <div className="space-y-2">
          {components.map(([type, metadata]) => 
            renderComponent(type, metadata)
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="h-full bg-white border-r border-gray-200 p-4 overflow-y-auto">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Components</h2>
          <span className="text-xs text-gray-500">Chat With AI</span>
        </div>
        <p className="text-sm text-gray-600 mt-1">Drag and drop to canvas</p>
      </div>

      <div className="space-y-6">
        {renderCategory(COMPONENT_CATEGORIES.INPUT, 'Input Components')}
        {renderCategory(COMPONENT_CATEGORIES.PROCESSING, 'Processing Components')}
        {renderCategory(COMPONENT_CATEGORIES.OUTPUT, 'Output Components')}
      </div>

      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <h4 className="text-sm font-medium text-blue-900 mb-2">
          💡 Pro Tip
        </h4>
        <p className="text-xs text-blue-700">
          Start with a User Query component and end with an Output component for a complete workflow.
        </p>
      </div>
    </div>
  );
};

export default ComponentLibrary;
