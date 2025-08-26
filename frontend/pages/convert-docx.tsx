import { useState } from 'react';
import { useRouter } from 'next/router';
import styles from '../styles/ConvertDocx.module.css';

export default function ConvertDocx() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isConverting, setIsConverting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const router = useRouter();

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Check if file is a DOCX file
      if (!file.name.toLowerCase().endsWith('.docx')) {
        setError('Please select a DOCX file');
        setSelectedFile(null);
        return;
      }
      
      setSelectedFile(file);
      setError(null);
      setSuccess(null);
    }
  };

  const handleConvert = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    setIsConverting(true);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('http://localhost:5557/convert-docx-to-markdown', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Conversion failed');
      }

      // Get the filename for download
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'converted.md';
      
      if (contentDisposition) {
        // Try different patterns for filename extraction
        const patterns = [
          /filename="([^"]+)"/,  // filename="example.docx"
          /filename=([^;]+)/,    // filename=example.docx
          /filename\*=UTF-8''([^;]+)/  // filename*=UTF-8''example.docx
        ];
        
        for (const pattern of patterns) {
          const match = contentDisposition.match(pattern);
          if (match) {
            filename = decodeURIComponent(match[1]);
            break;
          }
        }
      }
      
      // If we still don't have a proper filename, use the original file name with .md extension
      if (filename === 'converted.md' && selectedFile) {
        const originalName = selectedFile.name;
        const baseName = originalName.replace(/\.docx$/i, '');
        filename = `${baseName}.md`;
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setSuccess(`Successfully converted and downloaded ${filename}`);
      setSelectedFile(null);
      
      // Reset file input
      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) {
        fileInput.value = '';
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Conversion failed');
    } finally {
      setIsConverting(false);
    }
  };

  const handleBackToHome = () => {
    router.push('/');
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <button onClick={handleBackToHome} className={styles.backButton}>
          ← Back to AI Assistant
        </button>
        <h1 className={styles.title}>Convert DOCX to Markdown</h1>
        <p className={styles.subtitle}>
          Upload your DOCX files and convert them to Markdown format for easy editing and sharing.
        </p>
      </div>

      <div className={styles.uploadSection}>
        <div className={styles.uploadArea}>
          <input
            id="file-input"
            type="file"
            accept=".docx"
            onChange={handleFileSelect}
            className={styles.fileInput}
          />
          <label htmlFor="file-input" className={styles.fileLabel}>
            <div className={styles.uploadContent}>
              <div className={styles.uploadIcon}>📄</div>
              <div className={styles.uploadText}>
                {selectedFile ? (
                  <>
                    <strong>Selected: {selectedFile.name}</strong>
                    <span>Click to change file</span>
                  </>
                ) : (
                  <>
                    <strong>Choose a DOCX file</strong>
                    <span>or drag and drop here</span>
                  </>
                )}
              </div>
            </div>
          </label>
        </div>

        {selectedFile && (
          <div className={styles.fileInfo}>
            <div className={styles.fileDetails}>
              <span className={styles.fileName}>{selectedFile.name}</span>
              <span className={styles.fileSize}>
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </span>
            </div>
          </div>
        )}

        {error && (
          <div className={styles.error}>
            ❌ {error}
          </div>
        )}

        {success && (
          <div className={styles.success}>
            ✅ {success}
          </div>
        )}

        <button
          onClick={handleConvert}
          disabled={!selectedFile || isConverting}
          className={styles.convertButton}
        >
          {isConverting ? 'Converting...' : 'Convert to Markdown'}
        </button>
      </div>

      <div className={styles.infoSection}>
        <h2>How it works</h2>
        <div className={styles.steps}>
          <div className={styles.step}>
            <div className={styles.stepNumber}>1</div>
            <div className={styles.stepContent}>
              <h3>Upload DOCX File</h3>
              <p>Select your DOCX file using the upload area above</p>
            </div>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNumber}>2</div>
            <div className={styles.stepContent}>
              <h3>Convert to Markdown</h3>
              <p>Click the convert button to process your file</p>
            </div>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNumber}>3</div>
            <div className={styles.stepContent}>
              <h3>Download Result</h3>
              <p>Your Markdown file will be automatically downloaded</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
