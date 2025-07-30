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
}

export interface FullDocument {
  filename: string;
  content: string;
}
