export interface Source {
  filename: string;
  folder_path?: string;
  relevance: number;
  header?: string;
  content: string;
  full_document_available: boolean;
}

export interface Answer {
  answer: string;
  sources?: Source[];
  notice?: string;
  steps?: string[];
  method?: string;
  ai_used?: boolean;
  fallback_used?: boolean;
  fallback_reason?: string;
  model_used?: string;
  include_files?: boolean;
}

export interface FullDocument {
  filename: string;
  content: string;
}
