// Component Categories
export const COMPONENT_CATEGORIES = {
  INPUT: 'input',
  PROCESSING: 'processing',
  OUTPUT: 'output'
};

// Component Types
export const COMPONENT_TYPES = {
  USER_QUERY: 'user_query',
  KNOWLEDGE_BASE: 'knowledge_base',
  LLM_ENGINE: 'llm_engine',
  OUTPUT: 'output',
  DUMMY_A: 'dummy_a',
  DUMMY_B: 'dummy_b',
  DUMMY_C: 'dummy_c'
};

// Default Component Configurations
export const DEFAULT_COMPONENT_CONFIGS = {
  [COMPONENT_TYPES.USER_QUERY]: {
    placeholder: 'Enter your question here...',
    max_length: 1000
  },
  [COMPONENT_TYPES.KNOWLEDGE_BASE]: {
    chunk_size: 1000,
    chunk_overlap: 200,
    embedding_model: 'gemini',
    collection_name: 'default'
  },
  [COMPONENT_TYPES.LLM_ENGINE]: {
    model: 'gemini-pro',
    temperature: 0.7,
    max_tokens: 1000,
    use_web_search: false,
    custom_prompt: null
  },
  [COMPONENT_TYPES.OUTPUT]: {
    show_timestamps: true,
    enable_follow_up: true,
    max_history: 50
  },
  [COMPONENT_TYPES.DUMMY_A]: {},
  [COMPONENT_TYPES.DUMMY_B]: {},
  [COMPONENT_TYPES.DUMMY_C]: {}
};

// Component Metadata
export const COMPONENT_METADATA = {
  [COMPONENT_TYPES.USER_QUERY]: {
    label: 'User Query',
    description: 'Accepts user queries via a simple interface',
    icon: 'MessageSquare',
    category: COMPONENT_CATEGORIES.INPUT
  },
  [COMPONENT_TYPES.KNOWLEDGE_BASE]: {
    label: 'Knowledge Base',
    description: 'Processes documents and provides context',
    icon: 'Database',
    category: COMPONENT_CATEGORIES.PROCESSING
  },
  [COMPONENT_TYPES.LLM_ENGINE]: {
    label: 'LLM Engine',
    description: 'Generates responses using AI models',
    icon: 'Brain',
    category: COMPONENT_CATEGORIES.PROCESSING
  },
  [COMPONENT_TYPES.OUTPUT]: {
    label: 'Output',
    description: 'Displays the final response to the user',
    icon: 'Monitor',
    category: COMPONENT_CATEGORIES.OUTPUT
  },
  [COMPONENT_TYPES.DUMMY_A]: {
    label: 'Dummy A',
    description: 'Placeholder component (no behavior)',
    icon: 'Monitor',
    category: COMPONENT_CATEGORIES.PROCESSING
  },
  [COMPONENT_TYPES.DUMMY_B]: {
    label: 'Dummy B',
    description: 'Placeholder component (no behavior)',
    icon: 'Monitor',
    category: COMPONENT_CATEGORIES.PROCESSING
  },
  [COMPONENT_TYPES.DUMMY_C]: {
    label: 'Dummy C',
    description: 'Placeholder component (no behavior)',
    icon: 'Monitor',
    category: COMPONENT_CATEGORIES.PROCESSING
  }
};

// Workflow Validation Rules
export const WORKFLOW_VALIDATION_RULES = {
  MIN_NODES: 2,
  MAX_NODES: 20,
  REQUIRED_COMPONENTS: [COMPONENT_TYPES.USER_QUERY, COMPONENT_TYPES.OUTPUT]
};

// UI Constants
export const UI_CONSTANTS = {
  SIDEBAR_WIDTH: 280,
  CONFIG_PANEL_WIDTH: 320,
  MINIMAP_SIZE: 200,
  NODE_MIN_WIDTH: 150,
  NODE_MIN_HEIGHT: 80
};
