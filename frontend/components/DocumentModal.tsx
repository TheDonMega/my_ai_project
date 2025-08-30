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
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            backdrop-filter: blur(8px);
            animation: overlayFadeIn 0.3s ease-out;
          }

          @keyframes overlayFadeIn {
            from {
              opacity: 0;
            }
            to {
              opacity: 1;
            }
          }

          .modal {
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            border-radius: 20px;
            width: 90%;
            max-width: 900px;
            max-height: 90vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            animation: modalFadeIn 0.3s ease-out;
            border: 2px solid #e2e8f0;
          }

          @keyframes modalFadeIn {
            from {
              opacity: 0;
              transform: translateY(-30px) scale(0.95);
            }
            to {
              opacity: 1;
              transform: translateY(0) scale(1);
            }
          }

          .modal-header {
            padding: 24px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #e2e8f0;
            background: white;
            border-radius: 20px 20px 0 0;
          }

          .modal-header h2 {
            margin: 0;
            color: #2d3748;
            font-size: 1.4rem;
            font-weight: 700;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
          }

          .modal-header button {
            background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            font-size: 1.5rem;
            cursor: pointer;
            color: white;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(245, 101, 101, 0.3);
            font-weight: bold;
            line-height: 1;
          }

          .modal-header button:hover {
            background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
            transform: scale(1.1);
            box-shadow: 0 6px 16px rgba(245, 101, 101, 0.4);
          }

          .modal-content {
            padding: 32px;
            overflow-y: auto;
            max-height: calc(90vh - 100px);
            background: white;
            border-radius: 0 0 20px 20px;
          }

          .modal-content pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
            margin: 0;
            font-size: 14px;
            line-height: 1.6;
            color: #2d3748;
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
          }

          /* Custom scrollbar for modal content */
          .modal-content::-webkit-scrollbar {
            width: 10px;
          }

          .modal-content::-webkit-scrollbar-track {
            background: #f1f5f9;
            border-radius: 5px;
          }

          .modal-content::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #cbd5e0 0%, #a0aec0 100%);
            border-radius: 5px;
          }

          .modal-content::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #a0aec0 0%, #718096 100%);
          }

          /* Responsive design */
          @media (max-width: 768px) {
            .modal {
              width: 95%;
              max-height: 95vh;
            }
            
            .modal-header {
              padding: 20px 24px;
            }
            
            .modal-header h2 {
              font-size: 1.2rem;
            }
            
            .modal-content {
              padding: 24px;
              max-height: calc(95vh - 90px);
            }
            
            .modal-content pre {
              padding: 20px;
              font-size: 13px;
            }
          }
        `}</style>
      </div>
    </div>
  );
}
