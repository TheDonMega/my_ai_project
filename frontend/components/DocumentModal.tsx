import React, { useEffect, useRef } from 'react';
import type { FullDocument } from '../types';
import styles from './DocumentModal.module.css';

interface ModalProps {
  document: FullDocument | null;
  onClose: () => void;
}

export default function DocumentModal({ document: doc, onClose }: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  // Prevent background scroll when modal is open
  useEffect(() => {
    if (!doc) return;
    
    // Store current scroll position
    const scrollY = window.scrollY;
    
    // Prevent background scroll
    const originalOverflow = window.document.body.style.overflow;
    window.document.body.style.overflow = 'hidden';
    
    // Ensure modal is visible in viewport
    setTimeout(() => {
      if (modalRef.current) {
        modalRef.current.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center',
          inline: 'center'
        });
      }
    }, 100);
    
    return () => {
      window.document.body.style.overflow = originalOverflow;
      // Restore scroll position when modal closes
      window.scrollTo(0, scrollY);
    };
  }, [doc]);

  if (!doc) return null;

  return (
    <div 
      className={styles.modalOverlay} 
      onClick={onClose}
      style={{ zIndex: 999999, position: 'fixed' }}
    >
      <div 
        ref={modalRef}
        className={styles.modal} 
        onClick={(e) => e.stopPropagation()}
        style={{ zIndex: 999999 }}
      >
        <div className={styles.modalHeader}>
          <h2>{doc.filename}</h2>
          <button onClick={onClose} className={styles.closeButton}>&times;</button>
        </div>
        <div className={styles.modalContent}>
          <pre className={styles.documentContent}>{doc.content}</pre>
        </div>
      </div>
    </div>
  );
}
