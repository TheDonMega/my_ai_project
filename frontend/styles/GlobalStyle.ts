import { createGlobalStyle } from 'styled-components';

export const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
  }

  body {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
      'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
      sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    color: #2d3748;
    line-height: 1.6;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    margin-top: 20px;
    margin-bottom: 20px;
  }
  
  .status {
    margin-bottom: 20px;
    padding: 16px 20px;
    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    border-radius: 12px;
    color: #155724;
    border-left: 4px solid #28a745;
    font-weight: 500;
    box-shadow: 0 2px 8px rgba(40, 167, 69, 0.1);
  }
  
  textarea {
    width: 100%;
    padding: 16px;
    margin-bottom: 16px;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    font-size: 16px;
    transition: all 0.3s ease;
    background: #f8fafc;
    resize: vertical;
    min-height: 120px;
  }

  textarea:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    background: white;
  }
  
  button {
    padding: 12px 24px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    position: relative;
    overflow: hidden;
  }

  button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
  }

  button:active:not(:disabled) {
    transform: translateY(0);
  }
  
  button:disabled {
    background: linear-gradient(135deg, #a0aec0 0%, #718096 100%);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
  
  .processing {
    margin: 20px 0;
    padding: 20px;
    background: linear-gradient(135deg, #bee3f8 0%, #90cdf4 100%);
    border-radius: 12px;
    color: #2c5282;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-left: 4px solid #3182ce;
    box-shadow: 0 2px 8px rgba(49, 130, 206, 0.1);
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
    padding: 24px;
    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  }

  .sources {
    margin-top: 20px;
    border-top: 2px solid #e2e8f0;
    padding-top: 20px;
  }

  .sources-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .toggle-button {
    padding: 8px 16px;
    font-size: 14px;
    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    color: #4a5568;
    font-weight: 500;
    transition: all 0.3s ease;
  }

  .toggle-button:hover {
    background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
    border-color: #cbd5e0;
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
    background: white;
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    border: 1px solid #e2e8f0;
    transition: all 0.3s ease;
  }

  .source-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }

  .source-header {
    padding: 16px 20px;
    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .source-content {
    padding: 20px;
  }

  .source-content pre {
    background: #f7fafc;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
    margin-bottom: 12px;
    border: 1px solid #e2e8f0;
    font-size: 14px;
    line-height: 1.5;
  }

  .view-full-button {
    display: block;
    width: 100%;
    padding: 12px;
    text-align: center;
    background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 12px;
    cursor: pointer;
    font-weight: 500;
    color: #4a5568;
    transition: all 0.3s ease;
  }

  .view-full-button:hover {
    background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e0 100%);
    border-color: #a0aec0;
    color: #2d3748;
  }

  .relevance {
    margin-left: auto;
    color: #718096;
    font-size: 14px;
    font-weight: 500;
  }

  .notice {
    margin-top: 20px;
    padding: 16px 20px;
    background: linear-gradient(135deg, #fef5e7 0%, #fed7aa 100%);
    border: 1px solid #f6ad55;
    border-radius: 12px;
    color: #c05621;
    border-left: 4px solid #ed8936;
  }

  .follow-up {
    margin-top: 30px;
    padding: 24px;
    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
    border-radius: 16px;
    border: 1px solid #e2e8f0;
  }

  .follow-up-buttons {
    display: flex;
    gap: 12px;
    margin-top: 20px;
  }

  .follow-up-buttons button {
    flex: 1;
    padding: 12px 16px;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    background: white;
    color: #4a5568;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 500;
  }

  .follow-up-buttons button:hover {
    background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
    border-color: #cbd5e0;
    color: #2d3748;
  }

  /* Custom scrollbar */
  ::-webkit-scrollbar {
    width: 8px;
  }

  ::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #cbd5e0 0%, #a0aec0 100%);
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #a0aec0 0%, #718096 100%);
  }

  /* Focus styles for accessibility */
  *:focus {
    outline: 2px solid #667eea;
    outline-offset: 2px;
  }

  /* Selection styles */
  ::selection {
    background: rgba(102, 126, 234, 0.2);
    color: #2d3748;
  }

  /* Smooth transitions for all elements */
  * {
    transition: all 0.2s ease;
  }
`;
