import { useState, useEffect } from 'react';
import axios from 'axios';
import type { Answer, Source, FullDocument } from '../types.ts';
import DocumentModal from '../components/DocumentModal';
import FormattedAnswer from '../components/FormattedAnswer';
import styles from '../styles/Home.module.css';
import answerStyles from '../styles/Answer.module.css';
import stepStyles from '../styles/StepFlow.module.css';
import { GlobalStyle } from '../styles/GlobalStyle';

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
    setLoading(true);
    setAnswer(null);
    setProcessingStep('Searching knowledge base...');
    
    try {
      const response = await axios.post('http://localhost:5557/ask', { 
        question,
        step: 'initial'
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

  return (
    <div className={styles.container}>
      <h1>AI Knowledge Base Assistant</h1>
      
      {documentsLoaded !== null && (
        <div className={styles.status}>
          <p>Knowledge base loaded with {documentsLoaded} documents</p>
        </div>
      )}
      
      <form className={styles.questionForm} onSubmit={handleSubmit}>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask your question here..."
          rows={4}
        />
        <button className={styles.button} type="submit" disabled={loading}>
          {loading ? 'Processing...' : 'Ask Question'}
        </button>
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
                      <strong>{source.filename}</strong> 
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
        </div>
      )}
      
      <DocumentModal 
        document={selectedDocument}
        onClose={() => setSelectedDocument(null)}
      />


    </div>
  );
}
