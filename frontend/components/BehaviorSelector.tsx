import { useState, useEffect } from 'react';
import axios from 'axios';
import styles from './BehaviorSelector.module.css';

interface BehaviorFile {
  name: string;
  filename: string;
  description: string;
  preview: string;
}

interface BehaviorSelectorProps {
  onBehaviorSelect: (filename: string) => void;
  selectedBehavior: string | null;
  disabled?: boolean;
  compact?: boolean; // For use in QueryOptions
}

export default function BehaviorSelector({ 
  onBehaviorSelect, 
  selectedBehavior, 
  disabled = false,
  compact = false 
}: BehaviorSelectorProps) {
  const [behaviors, setBehaviors] = useState<BehaviorFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBehaviors = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('http://localhost:5557/behaviors');
      if (response.data.success) {
        setBehaviors(response.data.behaviors);
      } else {
        setError(response.data.error || 'Failed to fetch behaviors');
      }
    } catch (error) {
      setError('Error fetching behaviors: ' + (error as any).message);
      console.error('Error fetching behaviors:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBehaviorSelect = async (filename: string) => {
    try {
      setLoading(true);
      
      // Select the behavior
      await axios.post('http://localhost:5557/behaviors/select', {
        behavior_filename: filename
      });
      
      onBehaviorSelect(filename);
      setIsOpen(false);
      fetchBehaviors();
    } catch (error) {
      setError('Error selecting behavior: ' + (error as any).message);
      console.error('Error selecting behavior:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBehaviors();
  }, []);

  const getSelectedBehaviorInfo = () => {
    if (!selectedBehavior) return { name: 'Default', description: 'Standard helpful AI assistant behavior' };
    const behavior = behaviors.find(b => b.filename === selectedBehavior);
    return behavior || { name: selectedBehavior, description: 'Selected behavior' };
  };

  const selectedBehaviorInfo = getSelectedBehaviorInfo();

  if (compact) {
    return (
      <div className={styles.behaviorSelector}>
        <div className={styles.dropdownContainer}>
          <button
            className={styles.dropdownTrigger}
            onClick={() => setIsOpen(!isOpen)}
            disabled={disabled}
          >
            <div className={styles.selectedDisplay}>
              <span className={styles.selectedName}>{selectedBehaviorInfo.name}</span>
              <span className={styles.selectedDescription}>{selectedBehaviorInfo.description}</span>
            </div>
            <span className={`${styles.dropdownArrow} ${isOpen ? styles.open : ''}`}>▼</span>
          </button>

          {isOpen && (
            <div className={styles.dropdownMenu}>
              {loading && !behaviors.length && (
                <div className={styles.loading}>
                  <div className={styles.spinner}></div>
                  <span>Loading behaviors...</span>
                </div>
              )}

              {behaviors.length === 0 && !loading && (
                <div className={styles.noBehaviors}>
                  <p>No behaviors available</p>
                  <p>Add .md files to behavior_model/ folder</p>
                </div>
              )}

              {behaviors.length > 0 && (
                <div className={styles.behaviorList}>
                  {/* Default option */}
                  <div
                    className={`${styles.behaviorOption} ${!selectedBehavior ? styles.selected : ''}`}
                    onClick={() => handleBehaviorSelect('')}
                  >
                    <div className={styles.behaviorInfo}>
                      <div className={styles.behaviorHeader}>
                        <span className={styles.behaviorName}>Default</span>
                        <div className={styles.behaviorBadges}>
                          <span className={styles.badge}>Built-in</span>
                        </div>
                      </div>
                      <div className={styles.behaviorMeta}>
                        <span className={styles.behaviorDescription}>Standard helpful AI assistant</span>
                      </div>
                    </div>
                    
                    <div className={styles.behaviorActions}>
                      {!selectedBehavior && (
                        <span className={styles.checkmark}>✓</span>
                      )}
                    </div>
                  </div>

                  {behaviors.map((behavior) => (
                    <div
                      key={behavior.filename}
                      className={`${styles.behaviorOption} ${
                        selectedBehavior === behavior.filename ? styles.selected : ''
                      }`}
                      onClick={() => handleBehaviorSelect(behavior.filename)}
                    >
                      <div className={styles.behaviorInfo}>
                        <div className={styles.behaviorHeader}>
                          <span className={styles.behaviorName}>{behavior.name}</span>
                          <div className={styles.behaviorBadges}>
                            <span className={styles.badge}>Custom</span>
                          </div>
                        </div>
                        <div className={styles.behaviorMeta}>
                          <span className={styles.behaviorDescription}>{behavior.description}</span>
                        </div>
                      </div>
                      
                      <div className={styles.behaviorActions}>
                        {selectedBehavior === behavior.filename && (
                          <span className={styles.checkmark}>✓</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {behaviors.length > 0 && (
                <div className={styles.summary}>
                  <span>{behaviors.length + 1} behavior profiles available</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={styles.behaviorSelector}>
      <div className={styles.header}>
        <h3>🎭 Behavior Profile</h3>
        <div className={styles.headerButtons}>
          <button
            onClick={fetchBehaviors}
            className={styles.refreshButton}
            disabled={loading || disabled}
            title="Refresh behavior profiles"
          >
            {loading ? '🔄' : '↻'}
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

      <div className={styles.dropdownContainer}>
        <button
          className={styles.dropdownTrigger}
          onClick={() => setIsOpen(!isOpen)}
          disabled={disabled}
        >
          <div className={styles.selectedDisplay}>
            <span className={styles.selectedName}>{selectedBehaviorInfo.name}</span>
            <span className={styles.selectedDescription}>{selectedBehaviorInfo.description}</span>
          </div>
          <span className={`${styles.dropdownArrow} ${isOpen ? styles.open : ''}`}>▼</span>
        </button>

        {isOpen && (
          <div className={styles.dropdownMenu}>
            {loading && !behaviors.length && (
              <div className={styles.loading}>
                <div className={styles.spinner}></div>
                <span>Loading behavior profiles...</span>
              </div>
            )}

            {behaviors.length === 0 && !loading && (
              <div className={styles.noBehaviors}>
                <p>No behaviors available</p>
                <p>Add .md files to behavior_model/ folder</p>
              </div>
            )}

            {behaviors.length > 0 && (
              <div className={styles.behaviorList}>
                {/* Default option */}
                <div
                  className={`${styles.behaviorOption} ${!selectedBehavior ? styles.selected : ''}`}
                  onClick={() => handleBehaviorSelect('')}
                >
                  <div className={styles.behaviorInfo}>
                    <div className={styles.behaviorHeader}>
                      <span className={styles.behaviorName}>Default</span>
                      <div className={styles.behaviorBadges}>
                        <span className={styles.badge}>Built-in</span>
                      </div>
                    </div>
                    <div className={styles.behaviorMeta}>
                      <span className={styles.behaviorDescription}>Standard helpful AI assistant</span>
                    </div>
                  </div>
                  
                  <div className={styles.behaviorActions}>
                    {!selectedBehavior && (
                      <span className={styles.checkmark}>✓</span>
                    )}
                  </div>
                </div>

                {behaviors.map((behavior) => (
                  <div
                    key={behavior.filename}
                    className={`${styles.behaviorOption} ${
                      selectedBehavior === behavior.filename ? styles.selected : ''
                    }`}
                    onClick={() => handleBehaviorSelect(behavior.filename)}
                  >
                    <div className={styles.behaviorInfo}>
                      <div className={styles.behaviorHeader}>
                        <span className={styles.behaviorName}>{behavior.name}</span>
                        <div className={styles.behaviorBadges}>
                          <span className={styles.badge}>Custom</span>
                        </div>
                      </div>
                      <div className={styles.behaviorMeta}>
                        <span className={styles.behaviorDescription}>{behavior.description}</span>
                      </div>
                    </div>
                    
                    <div className={styles.behaviorActions}>
                      {selectedBehavior === behavior.filename && (
                        <span className={styles.checkmark}>✓</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {behaviors.length > 0 && (
              <div className={styles.summary}>
                <span>{behaviors.length + 1} behavior profiles available</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
