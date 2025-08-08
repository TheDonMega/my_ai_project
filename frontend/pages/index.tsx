import { useState, useEffect } from 'react';
import axios from 'axios';
import type { Answer, Source, FullDocument } from '../types.ts';
import DocumentModal from '../components/DocumentModal';
import FormattedAnswer from '../components/FormattedAnswer';
// FeedbackButton removed - not used in current interface
import ModelSelector from '../components/ModelSelector';
import QueryOptions from '../components/QueryOptions';
import styles from '../styles/Home.module.css';
import answerStyles from '../styles/Answer.module.css';

import { GlobalStyle } from '../styles/GlobalStyle';


;

export default function Home() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [loading, setLoading] = useState(false);
  const [documentsLoaded, setDocumentsLoaded] = useState<number | null>(null);
  const [processingStep, setProcessingStep] = useState<string>('');
  const [selectedDocument, setSelectedDocument] = useState<FullDocument | null>(null);
  const [showSections, setShowSections] = useState(true);
  const [viewingFullSource, setViewingFullSource] = useState(false);
  const [cliHistory, setCliHistory] = useState<Array<{type: 'input' | 'output', content: string, timestamp: Date}>>([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [trainingCollapsed, setTrainingCollapsed] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('trainingCollapsed') === 'true';
    }
    return false;
  });
  const [queryOptionsCollapsed, setQueryOptionsCollapsed] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('queryOptionsCollapsed') === 'true';
    }
    return false;
  });


  const [isTraining, setIsTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState<string>('');
  // Feedback notification removed - not used in current interface
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [includeFiles, setIncludeFiles] = useState<boolean>(true);

  // Check server status and get document count on load
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await axios.get('http://localhost:5557/status');
        setDocumentsLoaded(response.data.documents_loaded);
      } catch (error) {
        console.error('Error checking status:', error);
      }
    };
    checkStatus();
    
    // Add welcome message to CLI history
    const welcomeMessage = `Welcome to AI Assistant Terminal v1.0.0

Available commands:
- Type any question to get an AI response
- Press Enter to submit
- Model: ${selectedModel || 'Auto-select'}
- Files: ${includeFiles ? 'Included' : 'Not included'}

Ready for your first question!`;

    setCliHistory([{
      type: 'output',
      content: welcomeMessage,
      timestamp: new Date()
    }]);
  }, [selectedModel, includeFiles]);

  // Save collapse states to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('trainingCollapsed', trainingCollapsed.toString());
    }
  }, [trainingCollapsed]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('queryOptionsCollapsed', queryOptionsCollapsed.toString());
    }
  }, [queryOptionsCollapsed]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // This will be replaced by separate handlers
  };



  const handleCliSubmit = async (input: string) => {
    if (!input.trim()) return;
    
    // Add user input to CLI history
    const userEntry = { type: 'input' as const, content: input, timestamp: new Date() };
    setCliHistory(prev => [...prev, userEntry]);
    setCurrentInput('');
    
    // Start streaming response
    setIsStreaming(true);
    
    // Create initial output entry for streaming
    const outputEntry = { type: 'output' as const, content: '', timestamp: new Date() };
    setCliHistory(prev => [...prev, outputEntry]);
    
    try {
      const response = await fetch('http://localhost:5557/query-with-model-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          question: input,
          include_files: includeFiles,
          model_name: selectedModel
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No reader available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.error) {
                setCliHistory(prev => {
                  const newHistory = [...prev];
                  const lastEntry = newHistory[newHistory.length - 1];
                  if (lastEntry && lastEntry.type === 'output') {
                    lastEntry.content = `Error: ${data.error}`;
                  }
                  return newHistory;
                });
                break;
              }
              
              if (data.response) {
                // Update the last output entry incrementally
                setCliHistory(prev => {
                  const newHistory = [...prev];
                  const lastEntry = newHistory[newHistory.length - 1];
                  if (lastEntry && lastEntry.type === 'output') {
                    lastEntry.content += data.response;
                  }
                  return newHistory;
                });
                
                // Small delay to make streaming more visible
                await new Promise(resolve => setTimeout(resolve, 5));
              }
              
              if (data.done) {
                break;
              }
            } catch (e) {
              console.error('Error parsing streaming data:', e);
            }
          }
        }
      }
      
    } catch (error) {
      console.error('Error:', error);
      setCliHistory(prev => {
        const newHistory = [...prev];
        const lastEntry = newHistory[newHistory.length - 1];
        if (lastEntry && lastEntry.type === 'output') {
          lastEntry.content = 'Error occurred while streaming from model.';
        }
        return newHistory;
      });
    }
    
    setIsStreaming(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (currentInput.trim() && !isStreaming) {
        handleCliSubmit(currentInput);
      }
    }
  };

  const handleOllamaTraining = async () => {
    // Check if a model is selected
    if (!selectedModel) {
      setTrainingProgress('❌ Please select a model from the dropdown before training.');
      setTimeout(() => {
        setTrainingProgress('');
      }, 3000);
      return;
    }
    
    setIsTraining(true);
    setTrainingProgress(`Starting Ollama model training with ${selectedModel}...`);
    
    try {
      // Call the Ollama training endpoint with selected model
      const response = await axios.post('http://localhost:5557/train-ollama', {
        action: 'train_ollama',
        selected_model: selectedModel
      });
      
      if (response.data.success) {
        const trainedModelName = response.data.trained_model || `${selectedModel}-trained`;
        const action = response.data.model_exists ? 'Updated' : 'Created';
        setTrainingProgress(`✅ Ollama training completed! ${action} ${response.data.training_examples} training examples using ${selectedModel}. Model: ${trainedModelName}`);
        
        // Show success message for a few seconds
        setTimeout(() => {
          setTrainingProgress('');
        }, 8000);
      } else {
        setTrainingProgress('❌ Ollama training failed: ' + (response.data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Ollama training error:', error);
      setTrainingProgress('❌ Ollama training failed: ' + (error as any).message);
    } finally {
      setTimeout(() => {
        setIsTraining(false);
        setTrainingProgress('');
      }, 3000);
    }
  };

  return (
    <div className={styles.container}>
      <h1>AI Knowledge Base Assistant</h1>
      
      {/* Feedback notification removed - not used in current interface */}
      

      
      {documentsLoaded !== null && (
        <div className={styles.status}>
          <p>Knowledge base loaded with {documentsLoaded} documents</p>
        </div>
      )}

                {/* Ollama Training Section */}
          <div className={styles.trainingSection}>
            <div className={styles.trainingHeader}>
              <div className={styles.trainingTitle}>
                <button 
                  onClick={() => setTrainingCollapsed(!trainingCollapsed)}
                  className={styles.collapseButton}
                  title={trainingCollapsed ? "Expand training section" : "Collapse training section"}
                >
                  <span className={`${styles.collapseIcon} ${trainingCollapsed ? styles.collapsed : ''}`}>
                    ▼
                  </span>
                </button>
                <h3>Ollama Model Training</h3>
              </div>
              <button 
                onClick={handleOllamaTraining}
                disabled={isTraining}
                className={styles.trainingButton}
              >
                {isTraining ? 'Training...' : '🔄 Train Ollama Model'}
              </button>
            </div>
            
            <div className={`${styles.trainingContent} ${trainingCollapsed ? styles.collapsed : ''}`}>
              {isTraining && (
                <div className={styles.trainingProgress}>
                  <div className={styles.progressBar}>
                    <div className={styles.progressFill}></div>
                  </div>
                  <p>{trainingProgress}</p>
                </div>
              )}
              
              <div className={styles.trainingInfo}>
                <p>Train Ollama to better understand your knowledge base:</p>
                <ul>
                  <li>🧠 Improves response quality and accuracy</li>
                  <li>🎯 Adapts to your knowledge base content</li>
                  <li>⚡ Creates optimized training examples</li>
                  <li>📁 Saves Modelfile and training data to local_models/</li>
                  <li>⚠️ <strong>Select a model from the dropdown below before training</strong></li>
                </ul>
              </div>
            </div>
          </div>

      {/* Model Selection */}
      <ModelSelector
        onModelSelect={setSelectedModel}
        selectedModel={selectedModel}
        disabled={loading}
      />

      {/* Query Options */}
      <QueryOptions
        includeFiles={includeFiles}
        onIncludeFilesChange={setIncludeFiles}
        selectedModel={selectedModel}
        disabled={loading}
        collapsed={queryOptionsCollapsed}
        onToggleCollapse={() => setQueryOptionsCollapsed(!queryOptionsCollapsed)}
      />
      
      {/* CLI Interface */}
      <div className={styles.cliContainer}>
        <div className={styles.cliHeader}>
          <span className={styles.cliPrompt}>$</span>
          <span className={styles.cliTitle}>AI Assistant Terminal</span>
        </div>
        
        <div className={styles.cliOutput}>
          {cliHistory.map((entry, index) => (
            <div key={index} className={`${styles.cliEntry} ${styles[entry.type]}`}>
              {entry.type === 'input' && (
                <div className={styles.cliInput}>
                  <span className={styles.cliPrompt}>$</span>
                  <span className={styles.cliCommand}>{entry.content}</span>
                </div>
              )}
              {entry.type === 'output' && (
                <div className={styles.cliOutput}>
                  <pre className={styles.cliResponse}>{entry.content}</pre>
                </div>
              )}
            </div>
          ))}
          
          {isStreaming && (
            <div className={styles.cliEntry}>
              <div className={styles.cliOutput}>
                <span className={styles.cliCursor}>▋</span>
              </div>
            </div>
          )}
        </div>
        
        <div className={styles.cliInputContainer}>
          <span className={styles.cliPrompt}>$</span>
          <input
            type="text"
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your question and press Enter..."
            className={styles.cliInputField}
            disabled={isStreaming}
          />
        </div>
      </div>






      
      <DocumentModal 
        document={selectedDocument}
        onClose={() => setSelectedDocument(null)}
      />


    </div>
  );
}
