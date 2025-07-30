import { createGlobalStyle } from 'styled-components';

export const GlobalStyle = createGlobalStyle`
  .container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
  }
  
  .status {
    margin-bottom: 20px;
    padding: 10px;
    background-color: #e8f5e9;
    border-radius: 4px;
    color: #2e7d32;
  }
  
  textarea {
    width: 100%;
    padding: 10px;
    margin-bottom: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
  
  button {
    padding: 10px 20px;
    background-color: #0070f3;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  button:disabled {
    background-color: #ccc;
  }
  
  .processing {
    margin: 20px 0;
    padding: 15px;
    background-color: #e3f2fd;
    border-radius: 4px;
    color: #0d47a1;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .loading-dots:after {
    content: '...';
    animation: dots 1.5s steps(5, end) infinite;
  }
  
  @keyframes dots {
    0%, 20% { content: '.'; }
    40% { content: '..'; }
    60% { content: '...'; }
    80% { content: '....'; }
    100% { content: '.....'; }
  }
  
  .answer {
    margin-top: 20px;
    padding: 20px;
    background-color: #f7f7f7;
    border-radius: 4px;
  }

  .sources {
    margin-top: 20px;
    border-top: 1px solid #eaeaea;
    padding-top: 15px;
  }

  .sources-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
  }

  .toggle-button {
    padding: 5px 10px;
    font-size: 0.9em;
    background-color: #f0f0f0;
  }

  .sources-list {
    opacity: 1;
    max-height: 2000px;
    transition: all 0.3s ease-in-out;
  }

  .sources-list.collapsed {
    opacity: 0;
    max-height: 0;
    overflow: hidden;
  }

  .source-item {
    margin-bottom: 20px;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    overflow: hidden;
  }

  .source-header {
    padding: 12px 15px;
    background-color: #f8f9fa;
    border-bottom: 1px solid #eaeaea;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .source-content {
    padding: 15px;
  }

  .source-content pre {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 4px;
    overflow-x: auto;
    font-family: monospace;
    margin-bottom: 10px;
  }

  .view-full-button {
    display: block;
    width: 100%;
    padding: 8px;
    text-align: center;
    background-color: #e9ecef;
    border: none;
    border-radius: 4px;
    margin-top: 10px;
    cursor: pointer;
  }

  .view-full-button:hover {
    background-color: #dee2e6;
  }

  .relevance {
    margin-left: auto;
    color: #666;
    font-size: 0.9em;
  }

  .notice {
    margin-top: 15px;
    padding: 10px;
    background-color: #fff3cd;
    border: 1px solid #ffeeba;
    border-radius: 4px;
    color: #856404;
  }

  .follow-up {
    margin-top: 30px;
    padding: 20px;
    background-color: #f8f9fa;
    border-radius: 8px;
  }

  .follow-up-buttons {
    display: flex;
    gap: 10px;
    margin-top: 15px;
  }

  .follow-up-buttons button {
    flex: 1;
    padding: 10px;
    border: none;
    border-radius: 4px;
    background-color: #e9ecef;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .follow-up-buttons button:hover {
    background-color: #dee2e6;
  }
`;
