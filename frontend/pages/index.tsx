import { useState, useEffect } from 'react';
import axios from 'axios';
import type { Answer, Source, FullDocument } from '../types';
import DocumentModal from '../components/DocumentModal';
import FormattedAnswer from '../components/FormattedAnswer';
import styles from '../styles/Home.module.css';
import answerStyles from '../styles/Answer.module.css';
import { GlobalStyle } from '../styles/GlobalStyle';

export default function Home() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [loading, setLoading] = useState(false);
  const [documentsLoaded, setDocumentsLoaded] = useState<number | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<FullDocument | null>(null);
  const [showSections, setShowSections] = useState(true);
  const [isReindexing, setIsReindexing] = useState(false);
  const [reindexProgress, setReindexProgress] = useState<string>('');
  const [lastReindexTime, setLastReindexTime] = useState<string | null>(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await axios.get('http://localhost:5557/status');
        const stats = response.data.llamaindex_stats;
        if (stats && stats.indexing_stats) {
            setDocumentsLoaded(stats.indexing_stats.documents_processed);
        }
      } catch (error) {
        console.error('Error checking status:', error);
      }
    };
    checkStatus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    
    setLoading(true);
    setAnswer(null);
    
    try {
      const response = await axios.post('http://localhost:5557/ask', { 
        question,
      });
      
      setAnswer(response.data);
    } catch (error) {
      console.error('Error:', error);
      setAnswer({
        answer: 'Error occurred while fetching the answer.',
        sources: []
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReindex = async () => {
    setIsReindexing(true);
    setReindexProgress('Starting knowledge base re-indexing...');
    
    try {
      const response = await axios.post('http://localhost:5557/llamaindex/rebuild', {
        force_rebuild: true
      });
      
      if (response.data.success) {
        setReindexProgress('Re-indexing completed successfully!');
        setLastReindexTime(new Date().toLocaleString());
        
        if (response.data.stats && response.data.stats.documents_processed) {
            setDocumentsLoaded(response.data.stats.documents_processed);
        }
        
        setTimeout(() => {
          setReindexProgress('');
        }, 3000);
      } else {
        setReindexProgress('Re-indexing failed: ' + (response.data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Re-indexing error:', error);
      setReindexProgress('Re-indexing failed: ' + (error as any).message);
    } finally {
      setTimeout(() => {
        setIsReindexing(false);
        setReindexProgress('');
      }, 2000);
    }
  };

  return (
    <div className={styles.container}>
      <GlobalStyle />
      <h1>AI Knowledge Base Assistant</h1>
      
      {documentsLoaded !== null && (
        <div className={styles.status}>
          <p>Knowledge base loaded with {documentsLoaded} documents</p>
          {lastReindexTime && (
            <p className={styles.lastTraining}>Last re-indexed: {lastReindexTime}</p>
          )}
        </div>
      )}

      <div className={styles.trainingSection}>
          <div className={styles.trainingButtons}>
            <button 
              onClick={handleReindex}
              disabled={isReindexing}
              className={styles.trainingButton}
            >
              {isReindexing ? 'Re-indexing...' : '🔄 Re-index Knowledge Base'}
            </button>
          </div>
        {isReindexing && (
          <div className={styles.trainingProgress}>
            <p>{reindexProgress}</p>
          </div>
        )}
      </div>
      
      <form className={styles.form} onSubmit={handleSubmit}>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask your question here..."
          rows={4}
        />
        <div className={styles.buttonContainer}>
          <button 
            type="submit"
            className={styles.ollamaAnalysisButton} 
            disabled={loading || !question.trim()}
          >
            {loading ? 'Processing...' : 'Ask'}
          </button>
        </div>
      </form>

      {loading && (
        <div className={styles.processing}>
          <div className={styles.loadingDots}></div>
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
                      <strong>
                        {source.filename}
                      </strong> 
                      {source.score && <span className={answerStyles.relevance}>Relevance: {source.score.toFixed(2)}</span>}
                    </div>
                    
                    {showSections && (
                      <div className={answerStyles.sourceContent}>
                        <pre>{source.content}</pre>
                        <button
                          className={answerStyles.viewFullButton}
                          onClick={async () => {
                            // The document endpoint was removed, so we just show the content from the source
                            setSelectedDocument({
                                filename: source.filename,
                                content: source.content
                            });
                          }}
                        >
                          View Full Content
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
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
