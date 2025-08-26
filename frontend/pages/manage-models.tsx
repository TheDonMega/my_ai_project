import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import axios from 'axios';
import styles from '../styles/ManageModels.module.css';

interface Model {
  name: string;
  size: number;
  size_mb: number;
  size_gb: number;
  modified_at: string;
  is_running: boolean;
  is_trained: boolean;
  base_model: string;
  description: string;
}

export default function ManageModels() {
  const router = useRouter();
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [operationLoading, setOperationLoading] = useState<string | null>(null);
  const [operationMessage, setOperationMessage] = useState<string | null>(null);

  const fetchModels = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('http://localhost:5557/models');
      if (response.data.success) {
        setModels(response.data.models);
      } else {
        setError(response.data.error || 'Failed to fetch models');
      }
    } catch (error) {
      setError('Error fetching models: ' + (error as any).message);
      console.error('Error fetching models:', error);
    } finally {
      setLoading(false);
    }
  };

  const startModel = async (modelName: string) => {
    setOperationLoading(modelName + '-start');
    setOperationMessage(`Starting ${modelName}... This may take a moment while the model loads into memory.`);
    setError(null);
    
    try {
      const response = await axios.post(`http://localhost:5557/models/${encodeURIComponent(modelName)}/start`, {}, {
        timeout: 60000 // 60 second timeout for model starting
      });
      
      if (response.data.success) {
        setOperationMessage(`${modelName} is starting... Checking status...`);
        
        // Polling mechanism to check if model is actually running
        let attempts = 0;
        const maxAttempts = 10;
        const pollInterval = 2000; // 2 seconds
        
        const pollStatus = async () => {
          attempts++;
          try {
            const statusResponse = await axios.get('http://localhost:5557/models');
            if (statusResponse.data.success) {
              const updatedModels = statusResponse.data.models;
              const targetModel = updatedModels.find((m: any) => m.name === modelName);
              
              if (targetModel?.is_running) {
                setModels(updatedModels);
                setOperationMessage(`✅ ${modelName} started successfully!`);
                setTimeout(() => setOperationMessage(null), 3000);
                return true;
              } else if (attempts < maxAttempts) {
                setOperationMessage(`${modelName} is starting... (${attempts}/${maxAttempts})`);
                setTimeout(pollStatus, pollInterval);
                return false;
              } else {
                setOperationMessage(`⚠️ ${modelName} may have started but status is unclear. Please refresh to check.`);
                setTimeout(() => setOperationMessage(null), 5000);
                fetchModels();
                return true;
              }
            }
          } catch (pollError) {
            console.error('Error polling model status:', pollError);
          }
          return false;
        };
        
        // Start polling
        pollStatus();
      } else {
        setError(response.data.error || 'Failed to start model');
        setOperationMessage(null);
      }
    } catch (error) {
      if ((error as any).code === 'ECONNABORTED') {
        setError(`Starting ${modelName} is taking longer than expected. Please check back in a moment.`);
      } else {
        setError('Error starting model: ' + (error as any).message);
      }
      setOperationMessage(null);
      console.error('Error starting model:', error);
    } finally {
      setOperationLoading(null);
    }
  };

  const stopModel = async (modelName: string) => {
    setOperationLoading(modelName + '-stop');
    setOperationMessage(`Stopping ${modelName}... This may take up to 30 seconds as the model unloads from memory.`);
    setError(null);
    
    try {
      const response = await axios.post(`http://localhost:5557/models/${encodeURIComponent(modelName)}/stop`, {}, {
        timeout: 45000 // 45 second timeout for model stopping
      });
      
      if (response.data.success) {
        setOperationMessage(`${modelName} is stopping... Checking status...`);
        
        // Polling mechanism to check if model is actually stopped
        let attempts = 0;
        const maxAttempts = 15; // More attempts for stopping as it can take longer
        const pollInterval = 2000; // 2 seconds
        
        const pollStatus = async () => {
          attempts++;
          try {
            const statusResponse = await axios.get('http://localhost:5557/models');
            if (statusResponse.data.success) {
              const updatedModels = statusResponse.data.models;
              const targetModel = updatedModels.find((m: any) => m.name === modelName);
              
              if (!targetModel?.is_running) {
                setModels(updatedModels);
                setOperationMessage(`✅ ${modelName} stopped successfully!`);
                setTimeout(() => setOperationMessage(null), 3000);
                return true;
              } else if (attempts < maxAttempts) {
                setOperationMessage(`${modelName} is stopping... (${attempts}/${maxAttempts}) This can take a while...`);
                setTimeout(pollStatus, pollInterval);
                return false;
              } else {
                setOperationMessage(`⚠️ ${modelName} is taking longer than expected to stop. Please refresh to check status.`);
                setTimeout(() => setOperationMessage(null), 5000);
                fetchModels();
                return true;
              }
            }
          } catch (pollError) {
            console.error('Error polling model status:', pollError);
          }
          return false;
        };
        
        // Start polling
        pollStatus();
      } else {
        setError(response.data.error || 'Failed to stop model');
        setOperationMessage(null);
      }
    } catch (error) {
      if ((error as any).code === 'ECONNABORTED') {
        setError(`Stopping ${modelName} is taking longer than expected. The model may still be stopping in the background. Please check back in a moment.`);
      } else {
        setError('Error stopping model: ' + (error as any).message);
      }
      setOperationMessage(null);
      console.error('Error stopping model:', error);
    } finally {
      setOperationLoading(null);
    }
  };

  const deleteModel = async (modelName: string) => {
    // Find the model to check if it's trained
    const model = models.find(m => m.name === modelName);
    const isTrainedModel = model?.is_trained;
    
    let confirmMessage = `Are you sure you want to delete the model "${modelName}"?`;
    if (isTrainedModel) {
      confirmMessage += '\n\nThis is a trained model. Deleting it will also remove:';
      confirmMessage += '\n• Model-specific training data files';
      confirmMessage += '\n• Model configuration files';
      confirmMessage += '\n• All custom training work for this model';
      confirmMessage += '\n\nℹ️ Each model has its own independent training data.';
    }
    confirmMessage += '\n\nThis action cannot be undone.';
    
    if (!window.confirm(confirmMessage)) {
      return;
    }

    setOperationLoading(modelName + '-delete');
    let deleteMessage = `Deleting ${modelName}...`;
    if (isTrainedModel) {
      deleteMessage += ' This includes cleaning up all training files for this model.';
    }
    setOperationMessage(deleteMessage);
    setError(null);
    
    try {
      const response = await axios.delete(`http://localhost:5557/models/${encodeURIComponent(modelName)}/delete`);
      if (response.data.success) {
        if (isTrainedModel) {
          setOperationMessage(`✅ ${modelName} and all associated training files deleted successfully!`);
        } else {
          setOperationMessage(`✅ ${modelName} deleted successfully!`);
        }
        setTimeout(() => setOperationMessage(null), 4000);
        fetchModels();
      } else {
        setError(response.data.error || 'Failed to delete model');
        setOperationMessage(null);
      }
    } catch (error) {
      setError('Error deleting model: ' + (error as any).message);
      setOperationMessage(null);
      console.error('Error deleting model:', error);
    } finally {
      setOperationLoading(null);
    }
  };

  const cleanupOrphanedFiles = async () => {
    if (!window.confirm('Clean up orphaned training files?\n\nThis will remove training files from deleted models that are no longer needed.\n\nThis action cannot be undone.')) {
      return;
    }

    setOperationLoading('cleanup');
    setOperationMessage('Cleaning up orphaned training files...');
    setError(null);
    
    try {
      const response = await axios.post('http://localhost:5557/models/cleanup-orphaned-files');
      if (response.data.success) {
        const deletedCount = response.data.deleted_files.length;
        if (deletedCount > 0) {
          setOperationMessage(`✅ Cleaned up ${deletedCount} orphaned training files!`);
        } else {
          setOperationMessage('ℹ️ No orphaned files found to clean up.');
        }
        setTimeout(() => setOperationMessage(null), 4000);
      } else {
        setError(response.data.error || 'Failed to cleanup orphaned files');
        setOperationMessage(null);
      }
    } catch (error) {
      setError('Error cleaning up orphaned files: ' + (error as any).message);
      setOperationMessage(null);
      console.error('Error cleaning up orphaned files:', error);
    } finally {
      setOperationLoading(null);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return dateString;
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>🤖 Manage AI Models</h1>
        <div className={styles.headerActions}>
          <button
            onClick={cleanupOrphanedFiles}
            className={styles.cleanupButton}
            disabled={operationLoading === 'cleanup'}
            title="Clean up orphaned training files"
          >
            🧹 Cleanup
          </button>
          <button
            onClick={fetchModels}
            className={styles.refreshButton}
            disabled={loading}
            title="Refresh models"
          >
            {loading ? '🔄' : '↻'} Refresh
          </button>
          <button
            onClick={() => router.push('/')}
            className={styles.backButton}
            title="Back to main page"
          >
            ← Back
          </button>
        </div>
      </div>

      {error && (
        <div className={styles.error}>
          <span>❌ {error}</span>
          <button onClick={() => setError(null)} className={styles.closeError}>
            ×
          </button>
        </div>
      )}

      {operationMessage && (
        <div className={styles.operationMessage}>
          <span>ℹ️ {operationMessage}</span>
          <button onClick={() => setOperationMessage(null)} className={styles.closeMessage}>
            ×
          </button>
        </div>
      )}

      <div className={styles.summary}>
        <div className={styles.summaryCard}>
          <h3>Total Models</h3>
          <span className={styles.summaryNumber}>{models.length}</span>
        </div>
        <div className={styles.summaryCard}>
          <h3>Running Models</h3>
          <span className={styles.summaryNumber}>{models.filter(m => m.is_running).length}</span>
        </div>
        <div className={styles.summaryCard}>
          <h3>Trained Models</h3>
          <span className={styles.summaryNumber}>{models.filter(m => m.is_trained).length}</span>
        </div>
        <div className={styles.summaryCard}>
          <h3>Total Size</h3>
          <span className={styles.summaryNumber}>
            {formatFileSize(models.reduce((acc, m) => acc + m.size, 0))}
          </span>
        </div>
      </div>

      {loading && models.length === 0 ? (
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <span>Loading models...</span>
        </div>
      ) : models.length === 0 ? (
        <div className={styles.noModels}>
          <h3>No models found</h3>
          <p>No AI models are currently available. Models can be downloaded using <code>ollama pull &lt;model-name&gt;</code></p>
        </div>
      ) : (
        <div className={styles.modelGrid}>
          {models.map((model) => (
            <div key={model.name} className={`${styles.modelCard} ${model.is_running ? styles.running : ''}`}>
              <div className={styles.modelHeader}>
                <div className={styles.modelTitle}>
                  <h3>{model.name}</h3>
                  <div className={styles.modelBadges}>
                    {model.is_trained && <span className={styles.badge}>Trained</span>}
                    {model.is_running && <span className={styles.badge}>Running</span>}
                  </div>
                </div>
              </div>

              <div className={styles.modelInfo}>
                <div className={styles.infoRow}>
                  <span className={styles.label}>Size:</span>
                  <span className={styles.value}>{formatFileSize(model.size)}</span>
                </div>
                <div className={styles.infoRow}>
                  <span className={styles.label}>Base Model:</span>
                  <span className={styles.value}>{model.base_model || model.name}</span>
                </div>
                <div className={styles.infoRow}>
                  <span className={styles.label}>Modified:</span>
                  <span className={styles.value}>{formatDate(model.modified_at)}</span>
                </div>
                {model.description && (
                  <div className={styles.infoRow}>
                    <span className={styles.label}>Description:</span>
                    <span className={styles.value}>{model.description}</span>
                  </div>
                )}
              </div>

              <div className={styles.modelActions}>
                {model.is_running ? (
                  <button
                    onClick={() => stopModel(model.name)}
                    className={styles.stopButton}
                    disabled={operationLoading === model.name + '-stop'}
                    title={operationLoading === model.name + '-stop' ? "Stopping... This may take up to 30 seconds" : "Stop model"}
                  >
                    {operationLoading === model.name + '-stop' ? '🔄' : '⏹️'} 
                    {operationLoading === model.name + '-stop' ? ' Stopping...' : ' Stop'}
                  </button>
                ) : (
                  <button
                    onClick={() => startModel(model.name)}
                    className={styles.startButton}
                    disabled={operationLoading === model.name + '-start'}
                    title={operationLoading === model.name + '-start' ? "Starting... This may take a moment" : "Start model"}
                  >
                    {operationLoading === model.name + '-start' ? '🔄' : '▶️'} 
                    {operationLoading === model.name + '-start' ? ' Starting...' : ' Start'}
                  </button>
                )}

                <button
                  onClick={() => deleteModel(model.name)}
                  className={styles.deleteButton}
                  disabled={operationLoading === model.name + '-delete' || model.is_running}
                  title={
                    model.is_running 
                      ? "Stop model first to delete" 
                      : model.is_trained 
                        ? "Delete model and its independent training files" 
                        : "Delete model"
                  }
                >
                  {operationLoading === model.name + '-delete' ? '🔄' : '🗑️'} 
                  {operationLoading === model.name + '-delete' ? ' Deleting...' : ' Delete'}
                  {model.is_trained && !operationLoading && (
                    <span className={styles.trainedIndicator}> (+files)</span>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
