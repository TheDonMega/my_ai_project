interface Source {
  filename: string;
  relevance: number;
  header?: string;
}

interface Answer {
  answer: string;
  sources?: Source[];
  notice?: string;
}
