import { useState } from 'react';
import styles from './QueryOptions.module.css';

interface QueryOptionsProps {
  includeFiles: boolean;
  onIncludeFilesChange: (includeFiles: boolean) => void;
  selectedModel: string | null;
  disabled?: boolean;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export default function QueryOptions({ 
  includeFiles, 
  onIncludeFilesChange, 
  selectedModel, 
  disabled = false,
  collapsed = false,
  onToggleCollapse
}: QueryOptionsProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className={styles.queryOptions}>
      <div className={styles.header}>
        <div className={styles.headerTitle}>
          {onToggleCollapse && (
            <button 
              onClick={onToggleCollapse}
              className={styles.collapseButton}
              title={collapsed ? "Expand query options" : "Collapse query options"}
            >
              <span className={`${styles.collapseIcon} ${collapsed ? styles.collapsed : ''}`}>
                ▼
              </span>
            </button>
          )}
          <h4>Query Options</h4>
        </div>
      </div>
      
      <div className={`${styles.optionsContent} ${collapsed ? styles.collapsed : ''}`}>
        <div className={styles.optionsGrid}>
        <div className={styles.option}>
          <div className={styles.checkboxContainer}>
            <label htmlFor="includeFiles" className={styles.checkboxLabel}>
              <input
                type="checkbox"
                id="includeFiles"
                checked={includeFiles}
                onChange={(e) => onIncludeFilesChange(e.target.checked)}
                disabled={disabled}
                className={styles.checkbox}
              />
              <span className={styles.checkmark}></span>
              Include Knowledge Base Files
            </label>
            <button
              className={styles.helpButton}
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
              type="button"
            >
              ?
            </button>
          </div>
          
          {showTooltip && (
            <div className={styles.tooltip}>
              <p>
                <strong>Include Files:</strong> When enabled, the AI will search your knowledge base 
                and include relevant document content in its response.
              </p>
              <p>
                <strong>Disable for:</strong> General knowledge questions that don't require 
                your specific documents.
              </p>
              <p>
                <strong>Enable for:</strong> Questions about your specific content, documentation, 
                or any topic covered in your knowledge base.
              </p>
            </div>
          )}
          
          <div className={styles.optionDescription}>
            {includeFiles ? (
              <span className={styles.enabled}>
                ✓ AI will search and reference your knowledge base documents
              </span>
            ) : (
              <span className={styles.disabled}>
                ⚪ AI will use general knowledge only (faster responses)
              </span>
            )}
          </div>
        </div>

        <div className={styles.option}>
          <div className={styles.modelInfo}>
            <span className={styles.label}>Selected Model:</span>
            <span className={styles.value}>
              {selectedModel || 'Auto-select'}
            </span>
          </div>
          <div className={styles.optionDescription}>
            The AI model that will process your query
          </div>
        </div>
      </div>

      <div className={styles.performance}>
        <div className={styles.performanceGrid}>
          <div className={styles.performanceItem}>
            <span className={styles.performanceLabel}>Response Type:</span>
            <span className={styles.performanceValue}>
              {includeFiles ? 'Knowledge-Based' : 'General'}
            </span>
          </div>
          <div className={styles.performanceItem}>
            <span className={styles.performanceLabel}>Expected Speed:</span>
            <span className={styles.performanceValue}>
              {includeFiles ? 'Moderate (search + AI)' : 'Fast (AI only)'}
            </span>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}
