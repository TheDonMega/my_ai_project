import { useState, useEffect } from 'react';
import axios from 'axios';
import type { Answer, Source, FullDocument } from '../types.ts';
import DocumentModal from '../components/DocumentModal';
import FormattedAnswer from '../components/FormattedAnswer';
import FeedbackButton from '../components/FeedbackButton';
import styles from '../styles/Home.module.css';
import answerStyles from '../styles/Answer.module.css';
import stepStyles from '../styles/StepFlow.module.css';
import { GlobalStyle } from '../styles/GlobalStyle';
import TrainingDashboard from '../components/TrainingDashboard';

interface StepState {
  step: string;
  prompt: string;
  current_message?: string;
  message_to_send?: string;
  availableFiles?: string[];
  display_files?: string[];
  all_files_index?: string;
  files_to_include?: string[];
  selectedFiles?: string[];
  new_message?: string;
};

export default function Home() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [loading, setLoading] = useState(false);
  const [documentsLoaded, setDocumentsLoaded] = useState<number | null>(null);
  const [processingStep, setProcessingStep] = useState<string>('');
  const [selectedDocument, setSelectedDocument] = useState<FullDocument | null>(null);
  const [showSections, setShowSections] = useState(true);
  const [viewingFullSource, setViewingFullSource] = useState(false);
  const [currentStep, setCurrentStep] = useState<StepState | null>(null);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState<string>('');
  const [lastTrainingTime, setLastTrainingTime] = useState<string | null>(null);
  const [showTrainingDashboard, setShowTrainingDashboard] = useState(false);
  const [feedbackNotification, setFeedbackNotification] = useState<{
    show: boolean;
    message: string;
    type: 'success' | 'info' | 'warning';
    insights?: string[];
  } | null>(null);

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
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // This will be replaced by separate handlers
  };

  const handleAIAnalysis = async () => {
    if (!question.trim()) return;
    
    setLoading(true);
    setAnswer(null);
    setProcessingStep('Starting AI analysis...');
    
    try {
      const response = await axios.post('http://localhost:5557/ask', { 
        question,
        step: 'initial',
        method: 'ai_analysis'
      });
      
      if (response.data.steps) {
        for (const step of response.data.steps) {
          setProcessingStep(step);
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
      
      setAnswer(response.data);
      if (response.data.next_step) {
        setCurrentStep({
          step: response.data.next_step,
          prompt: response.data.prompt,
          current_message: question
        });
      }
    } catch (error) {
      console.error('Error:', error);
      setAnswer({
        answer: 'Error occurred while fetching the answer.',
        sources: []
      });
    } finally {
      setLoading(false);
      setProcessingStep('');
    }
  };

  const handleOllamaAnalysis = async () => {
    if (!question.trim()) return;
    
    setLoading(true);
    setAnswer(null);
    setProcessingStep('Analyzing with Ollama...');
    
    try {
      const response = await axios.post('http://localhost:5557/ask-ollama', { 
        question
      });
      
      setAnswer(response.data);
    } catch (error) {
      console.error('Error:', error);
      setAnswer({
        answer: 'Error occurred while fetching the answer from Ollama.',
        sources: []
      });
    }
    
    setProcessingStep('');
    setLoading(false);
  };

  const handleStepResponse = async (response: string) => {
    setLoading(true);
    
    try {
      if (!currentStep) return;

      const requestData: any = {
        question: currentStep.current_message,
        step: currentStep.step,
        confirm: response
      };

      if (currentStep.selectedFiles) {
        requestData.selected_files = currentStep.selectedFiles;
      }
      if (currentStep.files_to_include) {
        requestData.files_to_include = currentStep.files_to_include;
      }
      if (currentStep.new_message) {
        requestData.new_message = currentStep.new_message;
        requestData.message_to_send = currentStep.new_message;
      }
      if (currentStep.message_to_send) {
        requestData.message_to_send = currentStep.message_to_send;
      }

      // If this is the final confirmation step and user clicked "Send Request", 
      // immediately clear the currentStep to hide the buttons
      if (currentStep.step === 'confirm_request' && response === 'Y') {
        setCurrentStep(null);
      }

      const apiResponse = await axios.post('http://localhost:5557/ask', requestData);
      
      if (apiResponse.data.next_step) {
        setCurrentStep({
          ...currentStep,
          step: apiResponse.data.next_step,
          prompt: apiResponse.data.prompt,
          availableFiles: apiResponse.data.available_files,
          display_files: apiResponse.data.display_files,
          all_files_index: apiResponse.data.all_files_index,
          message_to_send: apiResponse.data.message_to_send,
          files_to_include: apiResponse.data.files_to_include || currentStep.files_to_include,
          selectedFiles: apiResponse.data.selectedFiles || currentStep.selectedFiles
        });
      } else {
        // Only set answer if there's actually an answer in the response
        if (apiResponse.data.answer) {
          setAnswer(apiResponse.data);
        }
        setCurrentStep(null);
      }
    } catch (error) {
      console.error('Error:', error);
      setAnswer({
        answer: 'Error occurred while processing the request.',
        sources: []
      });
      setCurrentStep(null);
    }
    
    setLoading(false);
  };

  const handleFileSelection = (selectedIndexes: string) => {
    const availableFiles = currentStep?.availableFiles;
    const allFilesIndex = currentStep?.all_files_index;
    if (!availableFiles?.length || !allFilesIndex) return;
    
    let selectedFiles: string[] = [];

    // Check if "All" option is selected
    if (selectedIndexes.split(',').map(i => i.trim()).includes(allFilesIndex)) {
      selectedFiles = availableFiles;
    } else {
      // Handle individual file selection
      selectedFiles = selectedIndexes.split(',').map(index => {
        const i = parseInt(index.trim()) - 1;
        return i >= 0 && i < availableFiles.length 
          ? availableFiles[i] 
          : null;
      }).filter((file): file is string => file !== null);
    }

    if (!currentStep) return;
    setCurrentStep({
      ...currentStep,
      selectedFiles: selectedFiles,
      files_to_include: selectedFiles  // Always set both fields
    });
  };

  const handleQuestionModification = (newQuestion: string) => {
    if (!currentStep) return;
    
    setCurrentStep({
      ...currentStep,
      new_message: newQuestion
    });
  };

  const handleTraining = async () => {
    setIsTraining(true);
    setTrainingProgress('Starting knowledge base training...');
    
    try {
      // Call the training endpoint
      const response = await axios.post('http://localhost:5557/train', {
        action: 'train_knowledge_base'
      });
      
      if (response.data.success) {
        setTrainingProgress('Training completed successfully!');
        setLastTrainingTime(new Date().toLocaleString());
        
        // Update document count if provided
        if (response.data.documents_processed) {
          setDocumentsLoaded(response.data.documents_processed);
        }
        
        // Show success message for a few seconds
        setTimeout(() => {
          setTrainingProgress('');
        }, 3000);
      } else {
        setTrainingProgress('Training failed: ' + (response.data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Training error:', error);
      setTrainingProgress('Training failed: ' + (error as any).message);
    } finally {
      setTimeout(() => {
        setIsTraining(false);
        setTrainingProgress('');
      }, 2000);
    }
  };

  const handleOllamaTraining = async () => {
    setIsTraining(true);
    setTrainingProgress('Starting Ollama model training...');
    
    try {
      // Call the Ollama training endpoint
      const response = await axios.post('http://localhost:5557/train-ollama', {
        action: 'train_ollama'
      });
      
      if (response.data.success) {
        setTrainingProgress(`Ollama training completed! Created ${response.data.training_examples} training examples.`);
        setLastTrainingTime(new Date().toLocaleString());
        
        // Show success message for a few seconds
        setTimeout(() => {
          setTrainingProgress('');
        }, 5000);
      } else {
        setTrainingProgress('Ollama training failed: ' + (response.data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Ollama training error:', error);
      setTrainingProgress('Ollama training failed: ' + (error as any).message);
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
      
      {/* Feedback Notification */}
      {feedbackNotification && feedbackNotification.show && (
        <div className={`mb-4 p-4 rounded-lg border ${
          feedbackNotification.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' :
          feedbackNotification.type === 'warning' ? 'bg-yellow-50 border-yellow-200 text-yellow-800' :
          'bg-blue-50 border-blue-200 text-blue-800'
        }`}>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="font-medium mb-2">{feedbackNotification.message}</h3>
              {feedbackNotification.insights && feedbackNotification.insights.length > 0 && (
                <div className="mt-3">
                  <p className="text-sm font-medium mb-2">How the system will learn:</p>
                  <ul className="space-y-1">
                    {feedbackNotification.insights.map((insight, index) => (
                      <li key={index} className="text-sm flex items-start">
                        <span className="mr-2">•</span>
                        {insight}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <button
              onClick={() => setFeedbackNotification(null)}
              className="ml-4 text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
        </div>
      )}
      
      <div className={styles.navigation}>
        <a href="/feedback" className={styles.navLink}>
          📊 View Feedback Analytics
        </a>
      </div>
      
      {documentsLoaded !== null && (
        <div className={styles.status}>
          <p>Knowledge base loaded with {documentsLoaded} documents</p>
          {lastTrainingTime && (
            <p className={styles.lastTraining}>Last trained: {lastTrainingTime}</p>
          )}
        </div>
      )}

      {/* Training Section */}
      <div className={styles.trainingSection}>
        <div className={styles.trainingHeader}>
          <h3>Knowledge Base Training</h3>
          <div className={styles.trainingButtons}>
            <button 
              onClick={handleTraining}
              disabled={isTraining}
              className={styles.trainingButton}
            >
              {isTraining ? 'Training...' : '🔄 Train Knowledge Base'}
            </button>
            <button 
              onClick={handleOllamaTraining}
              disabled={isTraining}
              className={styles.trainingButton}
            >
              {isTraining ? 'Training...' : '🔄 Train Ollama Model'}
            </button>
            <button 
              onClick={() => setShowTrainingDashboard(!showTrainingDashboard)}
              className={styles.dashboardButton}
            >
              📊 Training Dashboard
            </button>
          </div>
        </div>
        
        {isTraining && (
          <div className={styles.trainingProgress}>
            <div className={styles.progressBar}>
              <div className={styles.progressFill}></div>
            </div>
            <p>{trainingProgress}</p>
          </div>
        )}
        
        <div className={styles.trainingInfo}>
          <p>Training helps the AI understand your knowledge base better and improves search accuracy.</p>
          <ul>
            <li>📊 Indexes all documents for faster search</li>
            <li>🎯 Improves relevance scoring</li>
            <li>🧠 Creates semantic embeddings for better understanding</li>
            <li>📈 Tracks changes and updates automatically</li>
          </ul>
        </div>
      </div>
      
      {/* Training Dashboard */}
      {showTrainingDashboard && (
        <div className={styles.dashboardContainer}>
          <TrainingDashboard />
        </div>
      )}
      
      <form className={styles.form}>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask your question here..."
          rows={4}
        />
        <div className={styles.buttonContainer}>
          <button 
            type="button" 
            className={styles.aiAnalysisButton} 
            onClick={handleAIAnalysis}
            disabled={loading || !question.trim()}
          >
            {loading ? 'Processing...' : 'Use AI Locally'}
          </button>
          <button 
            type="button" 
            className={styles.ollamaAnalysisButton} 
            onClick={handleOllamaAnalysis}
            disabled={loading || !question.trim()}
          >
            {loading ? 'Processing...' : 'Use Ollama Locally'}
          </button>
        </div>
      </form>

      {processingStep && (
        <div className={styles.processing}>
          <p>{processingStep}</p>
          <div className={styles.loadingDots}></div>
        </div>
      )}

      {currentStep && (
        <div className={stepStyles.stepPrompt}>
          <h3>{currentStep.prompt}</h3>
          
          {currentStep.step === 'ask_ai' && (
            <div className={stepStyles.stepButtons}>
              <button onClick={() => handleStepResponse('Y')}>Yes</button>
              <button onClick={() => handleStepResponse('N')}>No</button>
            </div>
          )}

          {currentStep.step === 'select_markdown' && (
            <div className={stepStyles.stepButtons}>
              <button onClick={() => handleStepResponse('Y')}>Yes</button>
              <button onClick={() => handleStepResponse('N')}>No</button>
            </div>
          )}

          {/* Message modification prompt */}
          {currentStep.step === 'ask_modify_message' && (
            <div className={stepStyles.promptSection}>
              <p>{currentStep.prompt}</p>
              <div className={stepStyles.buttonContainer}>
                <button onClick={() => handleStepResponse('Y')} className={stepStyles.yesButton}>Yes, Update</button>
                <button onClick={() => handleStepResponse('N')} className={stepStyles.noButton}>No, Keep Current</button>
              </div>
            </div>
          )}

          {/* Enter new message */}
          {currentStep.step === 'enter_new_message' && (
            <div className={stepStyles.promptSection}>
              <p>{currentStep.prompt}</p>
              <div className={stepStyles.messagePreview}>
                <p>Current message:</p>
                <pre>{currentStep.current_message}</pre>
              </div>
              <div className={stepStyles.messageEdit}>
                <p>New message:</p>
                <textarea
                  defaultValue={currentStep.current_message}
                  onChange={(e) => setCurrentStep({
                    ...currentStep,
                    new_message: e.target.value,
                    message_to_send: e.target.value
                  })}
                  className={stepStyles.messageInput}
                  rows={4}
                />
              </div>
              <div className={stepStyles.buttonContainer}>
                <button onClick={() => handleStepResponse('continue')} className={stepStyles.submitButton}>Submit</button>
              </div>
            </div>
          )}

          {/* Include markdown prompt */}
          {currentStep.step === 'ask_include_markdown' && (
            <div className={stepStyles.promptSection}>
              <p>{currentStep.prompt}</p>
              <div className={stepStyles.buttonContainer}>
                <button onClick={() => handleStepResponse('Y')} className={stepStyles.yesButton}>Yes</button>
                <button onClick={() => handleStepResponse('N')} className={stepStyles.noButton}>No</button>
              </div>
            </div>
          )}

          {/* File selection */}
          {currentStep.step === 'select_markdown_files' && currentStep.availableFiles && (
            <div className={stepStyles.fileSelection}>
              <p>Available files:</p>
              <ul>
                {currentStep.display_files?.map((file, index) => (
                  <li key={index}>{file}</li>
                ))}
              </ul>
              <input
                type="text"
                placeholder="Enter file numbers (e.g., 1,2,3 or 4 for all)"
                onChange={(e) => handleFileSelection(e.target.value)}
                className={stepStyles.fileInput}
              />
              <div className={stepStyles.buttonContainer}>
                <button onClick={() => handleStepResponse('Y')} className={stepStyles.submitButton}>Continue</button>
              </div>
            </div>
          )}

          {currentStep.step === 'confirm_question' && (
            <div className={stepStyles.questionModification}>
              <p>Current question:</p>
              <pre>{currentStep.current_message}</pre>
              <textarea
                defaultValue={currentStep.current_message}
                onChange={(e) => handleQuestionModification(e.target.value)}
                rows={4}
                className={stepStyles.questionInput}
              />
              <div className={stepStyles.stepButtons}>
                <button onClick={() => handleStepResponse('continue')}>Continue with modified question</button>
                <button onClick={() => handleStepResponse('original')}>Use original question</button>
              </div>
            </div>
          )}

          {/* Final confirmation */}
          {currentStep.step === 'confirm_request' && (
            <div className={stepStyles.confirmationSection}>
              <h3>{currentStep.prompt}</h3>
              <div className={stepStyles.requestPreview}>
                <p><strong>Message to send:</strong></p>
                <pre>{currentStep.message_to_send || currentStep.current_message}</pre>
                
                {currentStep.files_to_include && currentStep.files_to_include.length > 0 && (
                  <>
                    <p><strong>Files to include:</strong></p>
                    <ul>
                      {currentStep.files_to_include.map((file, index) => (
                        <li key={index}>{file}</li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
              <div className={stepStyles.buttonContainer}>
                <button onClick={() => handleStepResponse('Y')} className={stepStyles.submitButton}>Send Request</button>
                <button onClick={() => handleStepResponse('N')} className={stepStyles.noButton}>Cancel</button>
              </div>
            </div>
          )}
        </div>
      )}

      {answer && (
        <div className={answerStyles.answer}>
          <h2>Answer:</h2>
          
          {/* AI Status Indicator */}
          {answer.ai_used !== undefined && (
            <div className={`${answerStyles.aiStatus} ${answer.ai_used ? answerStyles.aiSuccess : answerStyles.aiFallback}`}>
              {answer.ai_used ? (
                <div>
                  <span>🤖 AI Generated Response</span>
                  <span className={answerStyles.method}>Method: {answer.method}</span>
                </div>
              ) : (
                <div>
                  <span>⚠️ Local Search Fallback</span>
                  <span className={answerStyles.method}>Method: {answer.method}</span>
                  {answer.fallback_reason && (
                    <span className={answerStyles.fallbackReason}>Reason: {answer.fallback_reason}</span>
                  )}
                </div>
              )}
            </div>
          )}
          
          <FormattedAnswer answer={answer.answer} />
          
          {answer.sources && answer.sources.length > 0 && (
            <div className={answerStyles.sources}>
              <div className={answerStyles.sourcesHeader}>
                <h3>Sources:</h3>
                <button 
                  onClick={() => setShowSections(!showSections)}
                  className={answerStyles.toggleButton}
                >
                  {showSections ? 'Hide Sections' : 'Show Sections'}
                </button>
              </div>
              
              <div className={`${answerStyles.sourcesList} ${!showSections ? answerStyles.collapsed : ''}`}>
                {answer.sources.map((source: Source, index: number) => (
                  <div key={index} className={answerStyles.sourceItem}>
                    <div className={answerStyles.sourceHeader}>
                      <strong>
                        {source.folder_path && source.folder_path !== 'root' 
                          ? `${source.folder_path}/${source.filename.split('/').pop()}`
                          : source.filename
                        }
                      </strong> 
                      {source.folder_path && source.folder_path !== 'root' && (
                        <span className={answerStyles.folderPath}> (in {source.folder_path})</span>
                      )}
                      {source.header && <span> - {source.header}</span>}
                      <span className={answerStyles.relevance}>Relevance: {source.relevance}%</span>
                    </div>
                    
                    {showSections && (
                      <div className={answerStyles.sourceContent}>
                        <pre>{source.content}</pre>
                        {source.full_document_available && (
                          <button
                            className={answerStyles.viewFullButton}
                            onClick={async () => {
                              const response = await axios.get(`http://localhost:5557/document/${source.filename}`);
                              setSelectedDocument(response.data);
                            }}
                          >
                            View Full Document
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {answer.notice && (
            <div className={answerStyles.notice}>
              <p>{answer.notice}</p>
            </div>
          )}

          {/* Feedback Button */}
          <FeedbackButton
            userQuestion={question}
            aiResponse={answer.answer}
            searchMethod={answer.method || 'unknown'}
            sourcesUsed={answer.sources ? answer.sources.map(s => s.filename) : []}
            relevanceScore={answer.sources && answer.sources.length > 0 
              ? answer.sources.reduce((sum, s) => sum + (s.relevance || 0), 0) / answer.sources.length / 100
              : 0
            }
            onFeedbackSubmitted={(insights) => {
              setFeedbackNotification({
                show: true,
                message: '🎉 Feedback submitted! The system will learn from your input.',
                type: 'success',
                insights: insights
              });
              
              // Auto-hide after 8 seconds
              setTimeout(() => {
                setFeedbackNotification(null);
              }, 8000);
            }}
          />
        </div>
      )}
      
      <DocumentModal 
        document={selectedDocument}
        onClose={() => setSelectedDocument(null)}
      />


    </div>
  );
}
