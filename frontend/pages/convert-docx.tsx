import { useState } from 'react';
import { useRouter } from 'next/router';
import styles from '../styles/ConvertDocx.module.css';

export default function ConvertDocx() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isConverting, setIsConverting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const router = useRouter();

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length > 0) {
      // Check if all files are DOCX files
      const invalidFiles = files.filter(file => !file.name.toLowerCase().endsWith('.docx'));
      if (invalidFiles.length > 0) {
        setError(`Please select only DOCX files. Invalid files: ${invalidFiles.map(f => f.name).join(', ')}`);
        setSelectedFiles([]);
        return;
      }
      
      setSelectedFiles(files);
      setError(null);
      setSuccess(null);
    }
  };

  const handleConvert = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one file first');
      return;
    }

    setIsConverting(true);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });

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
      let filename = selectedFiles.length === 1 ? 'converted.md' : 'converted_files.zip';
      
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
      
      // If we still don't have a proper filename, create one based on files
      if (filename === 'converted.md' || filename === 'converted_files.zip') {
        if (selectedFiles.length === 1) {
          const originalName = selectedFiles[0].name;
          const baseName = originalName.replace(/\.docx$/i, '');
          filename = `${baseName}.md`;
        } else {
          // Create a zip filename based on the first file or use a generic name
          const firstFileName = selectedFiles[0].name.replace(/\.docx$/i, '');
          filename = `${firstFileName}_and_${selectedFiles.length - 1}_more_files.zip`;
        }
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

      const fileText = selectedFiles.length === 1 ? 'file' : 'files';
      setSuccess(`Successfully converted and downloaded ${selectedFiles.length} ${fileText} as ${filename}`);
      setSelectedFiles([]);
      
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
            multiple
            onChange={handleFileSelect}
            className={styles.fileInput}
          />
          <label htmlFor="file-input" className={styles.fileLabel}>
            <div className={styles.uploadContent}>
              <div className={styles.uploadIcon}>📄</div>
              <div className={styles.uploadText}>
                {selectedFiles.length > 0 ? (
                  <>
                    <strong>Selected: {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''}</strong>
                    <span>Click to change files</span>
                  </>
                ) : (
                  <>
                    <strong>Choose DOCX files</strong>
                    <span>or drag and drop here (multiple files supported)</span>
                  </>
                )}
              </div>
            </div>
          </label>
        </div>

        {selectedFiles.length > 0 && (
          <div className={styles.fileInfo}>
            <div className={styles.fileDetails}>
              {selectedFiles.map((file, index) => (
                <div key={index} className={styles.fileItem}>
                  <span className={styles.fileName}>{file.name}</span>
                  <span className={styles.fileSize}>
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </span>
                </div>
              ))}
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
          disabled={selectedFiles.length === 0 || isConverting}
          className={styles.convertButton}
        >
          {isConverting ? 'Converting...' : `Convert ${selectedFiles.length > 0 ? selectedFiles.length : ''} file${selectedFiles.length !== 1 ? 's' : ''} to Markdown`}
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
