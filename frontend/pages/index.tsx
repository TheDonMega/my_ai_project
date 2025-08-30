import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import axios from 'axios';
import type { Answer, Source, FullDocument } from '../types.ts';
import DocumentModal from '../components/DocumentModal';
import FormattedAnswer from '../components/FormattedAnswer';
// FeedbackButton removed - not used in current interface
import ModelSelector from '../components/ModelSelector';
import BehaviorSelector from '../components/BehaviorSelector';
import QueryOptions from '../components/QueryOptions';
import TrainingModal from '../components/TrainingModal';
import styles from '../styles/Home.module.css';
import answerStyles from '../styles/Answer.module.css';

import { GlobalStyle } from '../styles/GlobalStyle';


;

export default function Home() {
  const router = useRouter();
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
  const [currentStreamId, setCurrentStreamId] = useState<string | null>(null);
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
  const [selectedBehavior, setSelectedBehavior] = useState<string | null>(null);
  const [includeFiles, setIncludeFiles] = useState<boolean>(true);
  const [showTrainingModal, setShowTrainingModal] = useState(false);
  const [currentSources, setCurrentSources] = useState<Source[]>([]);
  const [showSources, setShowSources] = useState(false);

  const handleBehaviorSelect = async (behaviorFilename: string) => {
    try {
      await axios.post('http://localhost:5557/behaviors/select', {
        behavior_filename: behaviorFilename
      });
      setSelectedBehavior(behaviorFilename);
    } catch (error) {
      console.error('Error selecting behavior:', error);
    }
  };

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
    const getBehaviorDisplayName = () => {
      if (!selectedBehavior) return 'Default';
      // Extract a readable name from the behavior filename
      const name = selectedBehavior.replace('.md', '').replace('_', ' ').replace('-', ' ');
      return name.charAt(0).toUpperCase() + name.slice(1);
    };

    const welcomeMessage = `Welcome to AI Assistant Terminal v1.0.0

Available commands:
- Type any question to get an AI response
- Press Enter to submit
- Model: ${selectedModel || 'Auto-select'}
- Behavior Profile: ${getBehaviorDisplayName()}
- Files: ${includeFiles ? 'Included' : 'Not included'}

Ready for your first question!`;

    setCliHistory([{
      type: 'output',
      content: welcomeMessage,
      timestamp: new Date()
    }]);
  }, [selectedModel, selectedBehavior, includeFiles]);

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
    
    // Prevent multiple concurrent streams
    if (isStreaming) {
      console.log('Stream already in progress, ignoring new request');
      return;
    }
    
    // Generate unique stream ID
    const streamId = Date.now().toString() + Math.random().toString(36).substr(2, 9);
    setCurrentStreamId(streamId);
    
    // Add user input to CLI history
    const userEntry = { type: 'input' as const, content: input, timestamp: new Date() };
    setCliHistory(prev => [...prev, userEntry]);
    setCurrentInput('');
    
    // Start streaming response
    setIsStreaming(true);
    
    // Clear previous sources
    setCurrentSources([]);
    setShowSources(false);
    
    // Create initial output entry for streaming
    const outputEntry = { type: 'output' as const, content: '', timestamp: new Date() };
    setCliHistory(prev => [...prev, outputEntry]);
    
    try {
      console.log(`Starting stream ${streamId} for question: "${input}"`);
      
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
      let streamComplete = false;
      let responseLength = 0;

      while (!streamComplete) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log(`Stream ${streamId} reader done, processing final buffer`);
          // Process any remaining data in buffer before breaking
          if (buffer.trim()) {
            const lines = buffer.split('\n');
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  if (data.response) {
                    setCliHistory(prev => {
                      const newHistory = [...prev];
                      const lastEntry = newHistory[newHistory.length - 1];
                      if (lastEntry && lastEntry.type === 'output') {
                        const unescapedResponse = data.response
                          .replace(/\\"/g, '"')
                          .replace(/\\n/g, '\n');
                        lastEntry.content += unescapedResponse;
                        responseLength += unescapedResponse.length;
                      }
                      return newHistory;
                    });
                  }
                } catch (e) {
                  console.error('Error parsing final buffer data:', e, 'Line:', line);
                }
              }
            }
          }
          break;
        }
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.error) {
                console.log(`Stream ${streamId} error: ${data.error}`);
                setCliHistory(prev => {
                  const newHistory = [...prev];
                  const lastEntry = newHistory[newHistory.length - 1];
                  if (lastEntry && lastEntry.type === 'output') {
                    lastEntry.content = `Error: ${data.error}`;
                  }
                  return newHistory;
                });
                streamComplete = true;
                break;
              }
              
              // Capture sources from the first metadata message
              if (data.sources && data.model_used) {
                console.log('Sources data received:', data.sources);
                console.log('Sources filenames:', data.sources.map((s: any) => s.filename));
                setCurrentSources(data.sources);
                setShowSources(data.sources.length > 0);
                console.log(`Found ${data.sources.length} sources for query`);
              }
              
              if (data.response) {
                // Update the last output entry incrementally
                setCliHistory(prev => {
                  const newHistory = [...prev];
                  const lastEntry = newHistory[newHistory.length - 1];
                  if (lastEntry && lastEntry.type === 'output') {
                    // Unescape the response text
                    const unescapedResponse = data.response
                      .replace(/\\"/g, '"')
                      .replace(/\\n/g, '\n');
                    lastEntry.content += unescapedResponse;
                    responseLength += unescapedResponse.length;
                  }
                  return newHistory;
                });
                
                // Small delay to make streaming more visible
                await new Promise(resolve => setTimeout(resolve, 10));
              }
              
              if (data.done) {
                console.log(`Stream ${streamId} completed, total response length: ${responseLength} characters`);
                streamComplete = true;
                break;
              }
            } catch (e) {
              console.error('Error parsing streaming data:', e, 'Line:', line);
            }
          }
        }
        
        if (streamComplete) break;
      }
      
    } catch (error) {
      console.error(`Stream ${streamId} error:`, error);
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
    setCurrentStreamId(null);
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
    // Open the training modal directly
    setShowTrainingModal(true);
  };

  const handleViewDocument = async (filename: string) => {
    try {
      const response = await axios.get(`http://localhost:5557/document/${encodeURIComponent(filename)}`);
      const fullDocument: FullDocument = {
        filename,
        content: response.data.content
      };
      setSelectedDocument(fullDocument);
    } catch (error) {
      console.error('Error fetching document:', error);
    }
  };

  const handleTrainingStart = async (trainingData: any) => {
    setIsTraining(true);
    setTrainingProgress(`Starting custom training with ${trainingData.selected_files.length} files...`);
    
    try {
      const response = await axios.post('http://localhost:5557/train-ollama', trainingData);
      
      if (response.data.success) {
        setTrainingProgress(`✅ Custom training completed! Model: ${response.data.trained_model} (${response.data.training_examples} examples)`);
        
        // Show success message for a few seconds
        setTimeout(() => {
          setTrainingProgress('');
        }, 8000);
      } else {
        setTrainingProgress('❌ Training failed: ' + (response.data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Training error:', error);
      setTrainingProgress('❌ Training failed: ' + (error as any).message);
    } finally {
      setTimeout(() => {
        setIsTraining(false);
        setTrainingProgress('');
      }, 3000);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>AI Knowledge Base Assistant</h1>
        <div className={styles.convertButtons}>
          <button 
            onClick={() => router.push('/convert-docx')}
            className={styles.convertButton}
          >
            📄 Convert Notes to Markdown
          </button>
          <button 
            onClick={() => router.push('/convert-audio')}
            className={styles.convertButton}
          >
            🎵 Convert Audio to Markdown
          </button>
        </div>
      </div>
      
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
                {isTraining ? 'Training...' : '🎓 Train Custom Model'}
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
                <p>Create custom models with selective training:</p>
                <ul>
                  <li>🤖 <strong>Select base model</strong> from available models</li>
                  <li>📁 <strong>Choose specific files/folders</strong> from your knowledge base</li>
                  <li>🏷️ <strong>Custom model naming</strong> (e.g., technical-docs, customer-support)</li>
                  <li>🧠 Improves response quality for selected content</li>
                  <li>🎯 Each model has independent training data</li>
                  <li>⚡ Creates domain-specific AI assistants</li>
                  <li>✅ <strong>All-in-one interface</strong> - no need to pre-select model!</li>
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

      {/* Behavior Selection */}
      <BehaviorSelector
        onBehaviorSelect={handleBehaviorSelect}
        selectedBehavior={selectedBehavior}
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
          <div className={styles.cliStatus}>
            <span className={styles.cliStatusItem}>
              🎭 {selectedBehavior ? selectedBehavior.replace('.md', '').replace('_', ' ').replace('-', ' ') : 'Default'}
            </span>
            <span className={styles.cliStatusItem}>
              🤖 {selectedModel || 'Auto-select'}
            </span>
            <span className={styles.cliStatusItem}>
              📁 {includeFiles ? 'Files' : 'No Files'}
            </span>
          </div>
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

      {/* Sources Display */}
      {showSources && currentSources.length > 0 && (
        <div className={styles.sourcesContainer}>
          <div className={styles.sourcesHeader}>
            <h3>📁 Sources Found ({currentSources.length})</h3>
            <p>Files used to generate the response above:</p>
          </div>
          <div className={styles.sourcesList}>
            {currentSources.map((source, index) => (
              <div key={index} className={styles.sourceItem}>
                <div className={styles.sourceHeader}>
                  <div className={styles.sourceInfo}>
                    <span className={styles.sourceFilename}>{source.filename}</span>
                    {source.folder_path && (
                      <span className={styles.sourceFolder}>📁 {source.folder_path}</span>
                    )}
                    <span className={styles.sourceRelevance}>🎯 {source.relevance}% relevant</span>
                  </div>
                  <button
                    onClick={() => handleViewDocument(source.filename)}
                    className={styles.viewButton}
                  >
                    👁️ View Full File
                  </button>
                </div>
                <div className={styles.sourceContent}>
                  <div className={styles.sourceSection}>
                    <strong>Section:</strong> {source.header || 'No header'}
                  </div>
                  <div className={styles.sourcePreview}>
                    <strong>Preview:</strong> {source.content.substring(0, 200)}
                    {source.content.length > 200 && '...'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Document Modal */}
      {selectedDocument && (
        <DocumentModal
          document={selectedDocument}
          onClose={() => setSelectedDocument(null)}
        />
      )}

      {/* Training Modal */}
      {showTrainingModal && (
        <TrainingModal
          isOpen={showTrainingModal}
          onClose={() => setShowTrainingModal(false)}
          onTrainingStart={handleTrainingStart}
        />
      )}
    </div>
  );
}
