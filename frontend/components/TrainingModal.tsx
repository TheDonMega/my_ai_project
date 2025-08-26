import { useState, useEffect } from 'react';
import axios from 'axios';
import styles from '../styles/TrainingModal.module.css';
import BehaviorSelector from './BehaviorSelector';

interface FileItem {
  name: string;
  type: 'file' | 'directory';
  path: string;
  children?: FileItem[];
  file_count?: number;
  size?: number;
  modified?: string;
}

interface Model {
  name: string;
  is_running: boolean;
  is_trained: boolean;
  size?: string;
  modified?: string;
}

interface TrainingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTrainingStart: (data: any) => void;
}

export default function TrainingModal({ isOpen, onClose, onTrainingStart }: TrainingModalProps) {
  const [knowledgeBaseStructure, setKnowledgeBaseStructure] = useState<FileItem[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [customModelName, setCustomModelName] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [selectedBehavior, setSelectedBehavior] = useState('');
  const [availableModels, setAvailableModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(false);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (isOpen) {
      fetchKnowledgeBaseStructure();
      fetchAvailableModels();
      setSelectedFiles([]);
      setCustomModelName('');
      setSelectedModel('');
      setSelectedBehavior('');
      setError(null);
    }
  }, [isOpen]);

  const fetchKnowledgeBaseStructure = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:5557/knowledge-base/structure');
      if (response.data.success) {
        setKnowledgeBaseStructure(response.data.structure);
      } else {
        setError('Failed to load knowledge base structure');
      }
    } catch (error) {
      setError('Error loading knowledge base: ' + (error as any).message);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableModels = async () => {
    setModelsLoading(true);
    try {
      const response = await axios.get('http://localhost:5557/models');
      if (response.data && response.data.models) {
        // Filter out trained models, only show base models
        const baseModels = response.data.models.filter((model: Model) => 
          !model.is_trained && !model.name.includes('-')
        );
        setAvailableModels(baseModels);
        
        // Auto-select first available model if none selected
        if (baseModels.length > 0 && !selectedModel) {
          setSelectedModel(baseModels[0].name);
        }
      } else {
        setError('Failed to load available models');
      }
    } catch (error) {
      setError('Error loading models: ' + (error as any).message);
    } finally {
      setModelsLoading(false);
    }
  };

  const toggleFileSelection = (path: string, isDirectory: boolean = false) => {
    setSelectedFiles(prev => {
      if (prev.includes(path)) {
        // Remove file and any children if it's a directory
        return prev.filter(p => !p.startsWith(path));
      } else {
        // Add file
        const newSelection = [...prev, path];
        
        // If adding a directory, remove any individual files within it
        if (isDirectory) {
          return newSelection.filter(p => p === path || !p.startsWith(path + '/'));
        }
        
        return newSelection;
      }
    });
  };

  const toggleDirectoryExpansion = (path: string) => {
    setExpandedDirs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(path)) {
        newSet.delete(path);
      } else {
        newSet.add(path);
      }
      return newSet;
    });
  };

  const isFileSelected = (path: string): boolean => {
    return selectedFiles.includes(path) || selectedFiles.some(selected => path.startsWith(selected + '/'));
  };

  const isValidModelName = (name: string): boolean => {
    return /^[a-zA-Z0-9_-]+$/.test(name) && name.length > 0 && name.length <= 50;
  };

  const handleStartTraining = async () => {
    if (!selectedModel) {
      setError('Please select a base model for training');
      return;
    }

    if (!customModelName.trim()) {
      setError('Please enter a custom model name');
      return;
    }

    if (!isValidModelName(customModelName)) {
      setError('Model name can only contain letters, numbers, hyphens, and underscores (max 50 characters)');
      return;
    }

    if (selectedFiles.length === 0) {
      setError('Please select at least one file or folder for training');
      return;
    }

    const trainingData = {
      action: 'train_ollama',
      selected_model: selectedModel,
      selected_files: selectedFiles,
      custom_name: customModelName.trim(),
      behavior_filename: selectedBehavior || 'behavior.md'
    };

    onTrainingStart(trainingData);
    onClose();
  };

  const renderFileTree = (items: FileItem[], depth: number = 0): JSX.Element[] => {
    return items.map((item) => (
      <div key={item.path} className={styles.fileItem} style={{ marginLeft: `${depth * 20}px` }}>
        <div className={styles.fileRow}>
          {item.type === 'directory' && (
            <button
              className={styles.expandButton}
              onClick={() => toggleDirectoryExpansion(item.path)}
            >
              {expandedDirs.has(item.path) ? '▼' : '▶'}
            </button>
          )}
          
          <input
            type="checkbox"
            checked={isFileSelected(item.path)}
            onChange={() => toggleFileSelection(item.path, item.type === 'directory')}
            className={styles.checkbox}
          />
          
          <div className={styles.fileInfo}>
            <div className={styles.fileName}>
              {item.type === 'directory' ? '📁' : '📄'} {item.name}
            </div>
            <div className={styles.fileDetails}>
              {item.type === 'directory' 
                ? `${item.file_count || 0} files`
                : `${(item.size || 0 / 1024).toFixed(1)} KB`
              }
            </div>
          </div>
        </div>
        
        {item.type === 'directory' && 
         item.children && 
         expandedDirs.has(item.path) && 
         renderFileTree(item.children, depth + 1)}
      </div>
    ));
  };

  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        <div className={styles.modalHeader}>
          <h2>🎓 Train Custom Model</h2>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>

        <div className={styles.section}>
          <label className={styles.sectionTitle}>
            🤖 Select Base Model
            <span className={styles.required}>*</span>
          </label>
          {modelsLoading ? (
            <div className={styles.modelLoading}>Loading available models...</div>
          ) : (
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className={styles.modelSelect}
            >
              <option value="">Choose a base model...</option>
              {availableModels.map((model) => (
                <option key={model.name} value={model.name}>
                  {model.name} {model.is_running ? '(Running)' : ''}
                </option>
              ))}
            </select>
          )}
          <div className={styles.modelHelp}>
            Select the base model to train. Only non-trained models are shown.
          </div>
        </div>

        <div className={styles.section}>
          <BehaviorSelector
            onBehaviorSelect={setSelectedBehavior}
            selectedBehavior={selectedBehavior}
            disabled={false}
            compact={false}
          />
          <div className={styles.behaviorHelp}>
            Select the personality/behavior that will be embedded into the trained model.
          </div>
        </div>

        <div className={styles.section}>
          <label className={styles.sectionTitle}>
            🏷️ Custom Model Name
            <span className={styles.required}>*</span>
          </label>
          <input
            type="text"
            value={customModelName}
            onChange={(e) => setCustomModelName(e.target.value)}
            placeholder="e.g., technical-docs, customer-support, v2"
            className={styles.nameInput}
            maxLength={50}
          />
          <div className={styles.nameHelp}>
            Your model will be named: <code>{selectedModel ? selectedModel.replace(':', '_') : 'BASE_MODEL'}-{customModelName || 'CUSTOM_NAME'}</code>
          </div>
        </div>

        <div className={styles.section}>
          <label className={styles.sectionTitle}>
            📁 Select Files & Folders
            <span className={styles.required}>*</span>
          </label>
          
          <div className={styles.fileSelectionArea}>
            {selectedFiles.length > 0 && (
              <div className={styles.selectionSummary}>
                <strong>{selectedFiles.length} items selected</strong>
                <button 
                  onClick={() => setSelectedFiles([])}
                  className={styles.clearButton}
                >
                  Clear all
                </button>
              </div>
            )}

            <div className={styles.fileTree}>
              {loading ? (
                <div className={styles.loading}>Loading knowledge base...</div>
              ) : knowledgeBaseStructure.length === 0 ? (
                <div className={styles.empty}>
                  No files found in knowledge base. Add some .md files to get started.
                </div>
              ) : (
                renderFileTree(knowledgeBaseStructure)
              )}
            </div>
          </div>
        </div>

        {error && (
          <div className={styles.error}>
            ❌ {error}
          </div>
        )}

        <div className={styles.modalFooter}>
          <button onClick={onClose} className={styles.cancelButton}>
            Cancel
          </button>
          <button 
            onClick={handleStartTraining}
            className={styles.startButton}
            disabled={!selectedModel || !customModelName.trim() || selectedFiles.length === 0}
          >
            🚀 Start Training
          </button>
        </div>
      </div>
    </div>
  );
}
