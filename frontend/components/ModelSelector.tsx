import { useState, useEffect } from 'react';
import axios from 'axios';
import styles from './ModelSelector.module.css';

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

interface ModelSelectorProps {
  onModelSelect: (modelName: string) => void;
  selectedModel: string | null;
  disabled?: boolean;
}

export default function ModelSelector({ onModelSelect, selectedModel, disabled = false }: ModelSelectorProps) {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleModelSelect = async (modelName: string) => {
    try {
      const response = await axios.post('http://localhost:5557/models/select', {
        model_name: modelName
      });
      
      if (response.data.success) {
        onModelSelect(modelName);
        setIsOpen(false); // Close dropdown after selection
        fetchModels();
      } else {
        setError(response.data.error || 'Failed to select model');
      }
    } catch (error) {
      setError('Error selecting model: ' + (error as any).message);
      console.error('Error selecting model:', error);
    }
  };

  const startModel = async (modelName: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent dropdown from closing
    try {
      setLoading(true);
      const response = await axios.post(`http://localhost:5557/models/${encodeURIComponent(modelName)}/start`);
      
      if (response.data.success) {
        fetchModels();
      } else {
        setError(response.data.error || 'Failed to start model');
      }
    } catch (error) {
      setError('Error starting model: ' + (error as any).message);
      console.error('Error starting model:', error);
    } finally {
      setLoading(false);
    }
  };

  const stopModel = async (modelName: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent dropdown from closing
    try {
      setLoading(true);
      const response = await axios.post(`http://localhost:5557/models/${encodeURIComponent(modelName)}/stop`);
      
      if (response.data.success) {
        fetchModels();
      } else {
        setError(response.data.error || 'Failed to stop model');
      }
    } catch (error) {
      setError('Error stopping model: ' + (error as any).message);
      console.error('Error stopping model:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const formatFileSize = (bytes: number): string => {
    if (bytes >= 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
    } else if (bytes >= 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    } else {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
  };

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch {
      return dateString;
    }
  };

  const getSelectedModelInfo = () => {
    if (!selectedModel) return { name: 'Auto-select', description: 'System will choose the best available model' };
    const model = models.find(m => m.name === selectedModel);
    return model || { name: selectedModel, description: 'Selected model' };
  };

  const selectedModelInfo = getSelectedModelInfo();

  return (
    <div className={styles.modelSelector}>
      <div className={styles.header}>
        <h3>🤖 AI Model</h3>
        <button
          onClick={fetchModels}
          className={styles.refreshButton}
          disabled={loading || disabled}
          title="Refresh models"
        >
          {loading ? '🔄' : '↻'}
        </button>
      </div>

      {error && (
        <div className={styles.error}>
          <span>❌ {error}</span>
          <button onClick={() => setError(null)} className={styles.closeError}>
            ×
          </button>
        </div>
      )}

      <div className={styles.dropdownContainer}>
        <button
          className={styles.dropdownTrigger}
          onClick={() => setIsOpen(!isOpen)}
          disabled={disabled}
        >
          <div className={styles.selectedDisplay}>
            <span className={styles.selectedName}>{selectedModelInfo.name}</span>
            <span className={styles.selectedDescription}>{selectedModelInfo.description}</span>
          </div>
          <span className={`${styles.dropdownArrow} ${isOpen ? styles.open : ''}`}>▼</span>
        </button>

        {isOpen && (
          <div className={styles.dropdownMenu}>
            {loading && !models.length && (
              <div className={styles.loading}>
                <div className={styles.spinner}></div>
                <span>Loading models...</span>
              </div>
            )}

            {models.length === 0 && !loading && (
              <div className={styles.noModels}>
                <p>No models available</p>
                <p>Try: <code>ollama pull llama3.2:3b</code></p>
              </div>
            )}

            {models.length > 0 && (
              <div className={styles.modelList}>
                {models.map((model) => (
                  <div
                    key={model.name}
                    className={`${styles.modelOption} ${
                      selectedModel === model.name ? styles.selected : ''
                    } ${model.is_running ? styles.running : ''}`}
                    onClick={() => handleModelSelect(model.name)}
                  >
                    <div className={styles.modelInfo}>
                      <div className={styles.modelHeader}>
                        <span className={styles.modelName}>{model.name}</span>
                        <div className={styles.modelBadges}>
                          {model.is_trained && <span className={styles.badge}>Trained</span>}
                          {model.is_running && <span className={styles.badge}>Running</span>}
                        </div>
                      </div>
                      <div className={styles.modelMeta}>
                        <span className={styles.modelSize}>{formatFileSize(model.size)}</span>
                        <span className={styles.modelBase}>{model.base_model || model.name}</span>
                      </div>
                    </div>
                    
                    <div className={styles.modelActions}>
                      {selectedModel === model.name && (
                        <span className={styles.checkmark}>✓</span>
                      )}
                      {model.is_running ? (
                        <button
                          onClick={(e) => stopModel(model.name, e)}
                          className={styles.stopButton}
                          disabled={loading}
                          title="Stop model"
                        >
                          ⏹️
                        </button>
                      ) : (
                        <button
                          onClick={(e) => startModel(model.name, e)}
                          className={styles.startButton}
                          disabled={loading}
                          title="Start model"
                        >
                          ▶️
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {models.length > 0 && (
              <div className={styles.summary}>
                <span>{models.length} models • {models.filter(m => m.is_running).length} running</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
