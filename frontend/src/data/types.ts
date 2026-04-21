export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: string;
  grounded?: boolean;
  confidence?: number;
  activity?: ActivityStep[];
  followUpPrompts?: string[];
}

export interface Citation {
  index: number;
  source: string;
  title: string;
  page?: number;
  url: string;
  snippet?: string;
}

export interface ActivityStep {
  step: string;
  detail: string;
  duration_ms?: number;
  source?: string;
  reasoning_tree?: ReasoningNode[];
}

export interface ReasoningNode {
  label: string;
  children?: ReasoningNode[];
}

export interface Conversation {
  id: string;
  title: string;
  date: string;
  messageCount: number;
}

export interface SearchResult {
  content: string;
  score: number;
  source: string;
  title: string;
  page?: number;
  url: string;
}

export interface ChatResponse {
  response: string;
  citations: Citation[];
  conversation_id: string;
  grounded: boolean;
  confidence: number;
  activity?: ActivityStep[];
  follow_up_prompts?: string[];
}

export interface UserProfile {
  name: string;
  email: string;
  role: string;
  avatar?: string;
  department: string;
}

export interface SuggestedPrompt {
  text: string;
  icon: string;
}
