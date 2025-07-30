import React, { useEffect } from 'react';
import type { FullDocument } from '../types';

interface ModalProps {
  document: FullDocument | null;
  onClose: () => void;
}

export default function DocumentModal({ document: doc, onClose }: ModalProps) {
  // Prevent background scroll when modal is open
  useEffect(() => {
    if (!doc) return;
    const originalOverflow = window.document.body.style.overflow;
    window.document.body.style.overflow = 'hidden';
    return () => {
      window.document.body.style.overflow = originalOverflow;
    };
  }, [doc]);

  if (!doc) return null;

  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h2>{doc.filename}</h2>
          <button onClick={onClose}>&times;</button>
        </div>
        <div className="modal-content">
          <pre>{doc.content}</pre>
        </div>
        <style>{`
          .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.75);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            backdrop-filter: blur(2px);
          }

          .modal {
            background: white;
            border-radius: 12px;
            width: 90%;
            max-width: 800px;
            max-height: 90vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
            animation: modalFadeIn 0.2s ease-out;
          }

          @keyframes modalFadeIn {
            from {
              opacity: 0;
              transform: translateY(-20px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }

          .modal-header {
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #eaeaea;
          }

          .modal-header button {
            background: none;
            border: none;
            font-size: 1.75rem;
            cursor: pointer;
            padding: 0.5rem;
            color: #666;
            transition: color 0.2s;
            line-height: 1;
          }

          .modal-header button:hover {
            color: #000;
          }

          .modal-content {
            padding: 1.5rem;
            overflow-y: auto;
            max-height: calc(90vh - 70px); /* account for header height */
          }

          pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: monospace;
            margin: 0;
            font-size: 14px;
            line-height: 1.5;
          }
        `}</style>
      </div>
    </div>
  );
}
